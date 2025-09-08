# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
from collections.abc import AsyncGenerator, AsyncIterable
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

import fastapi
import httpx
from kink import inject

from beeai_server.api.schema.mcp import McpProvider, Resource, ResourceMeta, Tool, Toolkit
from beeai_server.configuration import Configuration
from beeai_server.domain.models.mcp_provider import (
    McpProviderDeploymentState,
    McpProviderLocation,
    McpProviderTransport,
)
from beeai_server.domain.models.user import User
from beeai_server.domain.utils import bridge_k8s_to_localhost, bridge_localhost_to_k8s
from beeai_server.exceptions import EntityNotFoundError, GatewayError, PlatformError
from beeai_server.service_layer.services.users import UserService

logger = logging.getLogger(__name__)


class McpServerResponse(NamedTuple):
    content: bytes | None
    stream: AsyncIterable | None
    status_code: int
    headers: dict[str, str] | None
    media_type: str


class ProxyRequestContext(NamedTuple):
    client: httpx.AsyncClient
    user: User


@inject
class McpService:
    STARTUP_TIMEOUT = timedelta(minutes=5)
    DUMMY_JWT_TOKEN = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCJ9.oqr2TWWCSPGG6fhGnnNjY9-vkDk1halSpcPkng9EFOY"
    )

    def __init__(
        self,
        user_service: UserService,
        configuration: Configuration,
    ):
        self._user_service = user_service
        self._config = configuration
        self._client = httpx.AsyncClient(base_url=str(self._config.mcp.gateway_endpoint_url), timeout=None)

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.__aexit__(exc_type, exc, tb)

    # Providers

    async def create_provider(
        self, *, name: str, location: McpProviderLocation, transport: McpProviderTransport
    ) -> McpProvider:
        async with self.gateway_context() as client:
            response = await client.post(
                "/gateways",
                json={
                    "name": name,
                    "url": str(bridge_localhost_to_k8s(location.root)),
                    "transport": self._provider_to_gateway_transport(transport),
                },
            )
            return self._gateway_to_provider(response.raise_for_status().json())

    async def list_providers(self) -> list[McpProvider]:
        async with self.gateway_context() as client:
            response = await client.get("/gateways")
            gateways: list[dict] = response.raise_for_status().json()
            return [self._gateway_to_provider(gateway) for gateway in gateways]

    async def read_provider(self, *, provider_id: str) -> McpProvider:
        async with self.gateway_context() as client:
            response = await client.get(f"/gateways/{provider_id}")
            return self._gateway_to_provider(response.raise_for_status().json())

    async def delete_provider(self, *, provider_id: str) -> None:
        async with self.gateway_context() as client:
            response = await client.delete(f"/gateways/{provider_id}")
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                if err.response.status_code == fastapi.status.HTTP_404_NOT_FOUND:
                    raise EntityNotFoundError("mcp_provider", provider_id) from err
                raise

    # Resources

    async def list_resources(self) -> list[ResourceMeta]:
        async with self.gateway_context() as client:
            response = await client.get("/resources")
            resources: list[dict] = response.raise_for_status().json()
            return [ResourceMeta.model_validate(resource) for resource in resources]

    async def read_resource(self, *, resource_id: str) -> Resource:
        resources = await self.list_resources()
        for resource in resources:
            if resource_id == resource.id:
                async with self.gateway_context() as client:
                    response = await client.get(f"/resources/{resource.uri}")
                    return Resource.model_validate(resource.model_dump() | response.raise_for_status().json())
        raise GatewayError(message=f"Resource {resource_id} not found", status_code=fastapi.status.HTTP_404_NOT_FOUND)

    # Tools

    async def list_tools(self) -> list[Tool]:
        async with self.gateway_context() as client:
            response = await client.get("/tools")
            tools: list[dict] = response.raise_for_status().json()
            return [Tool.model_validate(tool) for tool in tools]

    async def read_tool(self, *, tool_id: str) -> Tool:
        async with self.gateway_context() as client:
            response = await client.get(f"/tools/{tool_id}")
            return Tool.model_validate(response.raise_for_status().json())

    # Toolkits

    async def create_toolkit(self, *, tools: list[str]) -> Toolkit:
        async with self.gateway_context() as client:
            response = await client.post("/servers", json={"name": str(uuid.uuid4()), "associated_tools": tools})
            server = response.raise_for_status().json()

        id = server["id"]
        expires_at = datetime.now(UTC) + timedelta(seconds=self._config.mcp.toolkit_expiration_seconds)

        from beeai_server.jobs.tasks.mcp import delete_toolkit  # Avoid circual import

        await delete_toolkit.configure(queueing_lock=id, schedule_at=expires_at).defer_async(toolkit_id=id)

        return Toolkit(
            id=id,
            location=McpProviderLocation(f"http://{self._config.platform_service_url}/api/v1/mcp/toolkits/{id}/mcp"),
            transport=McpProviderTransport.STREAMABLE_HTTP,
            expires_at=expires_at,
        )

    async def delete_toolkit(self, *, toolkit_id: str) -> None:
        async with self.gateway_context() as client:
            response = await client.delete(f"/servers/{toolkit_id}")
            response.raise_for_status()

    # MCP Forwarding

    async def streamable_http_proxy(self, request: fastapi.Request, *, toolkit_id: str | None) -> McpServerResponse:
        exit_stack = AsyncExitStack()
        try:
            resp: httpx.Response = await exit_stack.enter_async_context(
                self._client.stream(
                    request.method,
                    f"/servers/{toolkit_id}/mcp" if toolkit_id else "/mcp",
                    data=await request.body(),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.DUMMY_JWT_TOKEN}",
                        "Accept": "application/json, text/event-stream",
                    },
                    follow_redirects=True,
                )
            )

            is_stream = resp.headers["content-type"].startswith("text/event-stream")

            async def stream_fn():
                try:
                    async for event in resp.stream:
                        yield event
                finally:
                    await exit_stack.pop_all().aclose()

            common = {
                "status_code": resp.status_code,
                "headers": resp.headers,
                "media_type": resp.headers["content-type"],
            }
            if is_stream:
                return McpServerResponse(content=None, stream=stream_fn(), **common)
            else:
                try:
                    await resp.aread()
                    return McpServerResponse(stream=None, content=resp.content, **common)
                finally:
                    await exit_stack.pop_all().aclose()
        except BaseException:
            await exit_stack.pop_all().aclose()
            raise

    def _gateway_to_provider(self, gateway: dict) -> McpProvider:
        return McpProvider(
            id=gateway["id"] or "missing-bug",  # TODO remove once fixed
            name=gateway["name"],
            location=McpProviderLocation(bridge_k8s_to_localhost(gateway["url"])),
            transport=self._gateway_to_provider_transport(gateway),
            state=self._gateway_to_provider_status(gateway),
        )

    def _gateway_to_provider_status(self, gateway: dict) -> McpProviderDeploymentState:
        if gateway["reachable"]:
            return McpProviderDeploymentState.RUNNING
        else:
            return McpProviderDeploymentState.MISSING

    def _gateway_to_provider_transport(self, gateway: dict) -> McpProviderDeploymentState:
        match gateway["transport"]:
            case "SSE":
                return McpProviderTransport.SSE
            case "STREAMABLEHTTP":
                return McpProviderTransport.STREAMABLE_HTTP

    def _provider_to_gateway_transport(self, transport: McpProviderTransport) -> str:
        match transport:
            case McpProviderTransport.SSE:
                return "SSE"
            case McpProviderTransport.STREAMABLE_HTTP:
                return "STREAMABLEHTTP"

    @asynccontextmanager
    async def gateway_context(self) -> AsyncGenerator[httpx.AsyncClient]:
        try:
            yield self._client
        except httpx.HTTPStatusError as err:
            if err.response.status_code in {fastapi.status.HTTP_400_BAD_REQUEST, fastapi.status.HTTP_404_NOT_FOUND}:
                raise GatewayError(message=await err.response.aread(), status_code=err.response.status_code) from err
            logger.error(
                "Status Error during Gateway context: %s - %s", err.response.status_code, await err.response.aread()
            )
            raise PlatformError() from err
        except httpx.RequestError as err:
            logger.error("Request error during Gateway context: %s", err)
            raise GatewayError(status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE) from err
        except ValueError as err:
            # JSON decode error
            logger.error("Error during Gateway context: %s", err)
            raise GatewayError(
                "Invalid response from upstream server",
                status_code=fastapi.status.HTTP_502_BAD_GATEWAY,
            ) from err
        except Exception as err:
            logger.error("Error during Gateway context: %s", err)
            raise PlatformError() from err
