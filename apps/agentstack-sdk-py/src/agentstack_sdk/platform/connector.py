# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import asyncio
import webbrowser
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

import pydantic
from pydantic import AnyUrl, BeforeValidator, Field

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.platform.common import PaginatedResult
from agentstack_sdk.platform.types import Metadata


def uuid_to_str(v: UUID | str) -> str:
    """Convert UUID or str to str."""
    if isinstance(v, UUID):
        return str(v)
    return v


UuidStr = Annotated[UUID | str, BeforeValidator(uuid_to_str)]


class AuthorizationCodeRequest(pydantic.BaseModel):
    """Authorization request for code-based OAuth flow."""

    type: Literal["code"] = "code"
    authorization_endpoint: AnyUrl


class ConnectorPreset(pydantic.BaseModel):
    """Represents a preset connector configuration."""

    url: AnyUrl
    metadata: Metadata | None = None


class ConnectorState(StrEnum):
    """Enumeration of possible connector states."""

    created = "created"
    auth_required = "auth_required"
    connected = "connected"
    disconnected = "disconnected"


class MCPProxyResponse(pydantic.BaseModel):
    """Response from an MCP proxy request with headers and streaming content."""

    headers: Annotated[dict[str, str], Field(description="HTTP headers from the proxy response")]
    status_code: Annotated[int, Field(description="HTTP status code from the proxy response")]
    chunk: Annotated[bytes, Field(description="Bytes chunk from streaming response content")]


class Connector(pydantic.BaseModel):
    """Represents a configured connector instance."""

    id: UUID
    url: AnyUrl
    state: ConnectorState
    auth_request: AuthorizationCodeRequest | None = None
    disconnect_reason: str | None = None
    metadata: Metadata | None = None
    created_at: pydantic.AwareDatetime | None = None
    updated_at: pydantic.AwareDatetime | None = None
    created_by: UUID | None = None

    @staticmethod
    async def create(
        url: AnyUrl | str,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        metadata: Metadata | None = None,
        match_preset: bool = True,
        client: PlatformClient | None = None,
    ) -> "Connector":
        """
        Create a new connector.

        Args:
            url: The URL of the connector/MCP server
            client_id: OAuth client ID (optional)
            client_secret: OAuth client secret (optional)
            metadata: Additional metadata for the connector (optional)
            match_preset: Whether to match against preset connectors
            client: Optional PlatformClient instance

        Returns:
            The created Connector instance
        """
        async with client or get_platform_client() as client:
            response = await client.post(
                url="/api/v1/connectors",
                json={
                    "url": str(url),
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "metadata": metadata,
                    "match_preset": match_preset,
                },
            )
            response.raise_for_status()
            return pydantic.TypeAdapter(Connector).validate_python(response.json())

    @staticmethod
    async def list(
        *,
        client: PlatformClient | None = None,
    ) -> PaginatedResult["Connector"]:
        """
        List all connectors for the current user.

        Returns:
            A paginated list of Connector instances
        """
        async with client or get_platform_client() as client:
            response = await client.get(url="/api/v1/connectors")
            response.raise_for_status()
            return pydantic.TypeAdapter(PaginatedResult[Connector]).validate_python(response.json())

    async def get(
        self: "Connector" | UuidStr,
        *,
        client: PlatformClient | None = None,
    ) -> "Connector":
        """
        Read a specific connector by ID.
        """
        connector_id = str(self.id) if isinstance(self, Connector) else self
        async with client or get_platform_client() as client:
            response = await client.get(url=f"/api/v1/connectors/{connector_id}")
            response.raise_for_status()
            return pydantic.TypeAdapter(Connector).validate_python(response.json())

    async def delete(
        self: "Connector" | UuidStr,
        *,
        client: PlatformClient | None = None,
    ) -> None:
        """
        Delete a connector.

        Args:
            client: Optional PlatformClient instance
        """
        connector_id = str(self.id) if isinstance(self, Connector) else self
        async with client or get_platform_client() as client:
            response = await client.delete(url=f"/api/v1/connectors/{connector_id}")
            response.raise_for_status()

    async def refresh(
        self: "Connector" | UuidStr,
        *,
        client: PlatformClient | None = None,
    ) -> "Connector":
        """
        This is just a syntactic sugar for calling Connector.get().
        """
        async with client or get_platform_client() as client:
            return await Connector.get(self, client=client)

    async def wait_for_state(
        self: "Connector" | UuidStr,
        *,
        state: ConnectorState = ConnectorState.connected,
        poll_interval: int = 1,
        client: PlatformClient | None = None,
    ) -> "Connector":
        """
        Wait for the connector to reach connected state.

        This is useful after calling connect() and opening the browser for OAuth.
        It will poll the server until the connector reaches 'connected' state or
        timeout is exceeded.

        Args:
            poll_interval: Seconds between polls (default: 2)
            client: Optional PlatformClient instance

        Returns:
            Updated Connector instance when connected

        Raises:
            TimeoutError: If connector doesn't reach connected state within timeout (300 seconds)
        """
        async with client or get_platform_client() as client:
            connector = self if isinstance(self, Connector) else await Connector.get(self, client=client)

            async with asyncio.timeout(300):
                while connector.state != state:
                    await asyncio.sleep(poll_interval)
                    connector = await connector.refresh(client=client)
            return connector

    async def wait_for_deletion(
        self: "Connector" | UuidStr,
        *,
        poll_interval: int = 1,
        client: PlatformClient | None = None,
    ) -> None:
        connector_id = str(self.id) if isinstance(self, Connector) else self
        async with client or get_platform_client() as client:
            async with asyncio.timeout(30):
                while True:
                    connector_list = await Connector.list(client=client)
                    if not any(str(conn.id) == connector_id for conn in connector_list.items):
                        return
                    await asyncio.sleep(poll_interval)

    async def connect(
        self: "Connector" | UuidStr,
        *,
        redirect_url: AnyUrl | str | None = None,
        access_token: str | None = None,
        client: PlatformClient | None = None,
    ) -> "Connector":
        """
        Connect a connector (establish authorization).

        If the connector requires OAuth authorization, this will automatically
        open the browser with the authorization endpoint.

        Args:
            redirect_url: OAuth redirect URL (optional)
            access_token: OAuth access token (optional)
            client: Optional PlatformClient instance

        Returns:
            The updated Connector instance
        """
        connector_id = str(self.id) if isinstance(self, Connector) else self
        async with client or get_platform_client() as client:
            response = await client.post(
                url=f"/api/v1/connectors/{connector_id}/connect",
                json={
                    "redirect_url": str(redirect_url) if redirect_url else None,
                    "access_token": access_token,
                },
            )
            response.raise_for_status()
            connector = pydantic.TypeAdapter(Connector).validate_python(response.json())
        # If auth is required, open the browser automatically and returns the connector in
        # `auth_required` state
        if connector.state == ConnectorState.auth_required and connector.auth_request:
            webbrowser.open(connector.auth_request.authorization_endpoint.unicode_string(), new=2)

        return connector

    async def disconnect(
        self: "Connector" | UuidStr,
        *,
        client: PlatformClient | None = None,
    ) -> "Connector":
        """
        Disconnect a connector.

        Args:
            client: Optional PlatformClient instance

        Returns:
            The updated Connector instance
        """
        connector_id = str(self.id) if isinstance(self, Connector) else self
        async with client or get_platform_client() as client:
            response = await client.post(url=f"/api/v1/connectors/{connector_id}/disconnect")
            response.raise_for_status()
            return pydantic.TypeAdapter(Connector).validate_python(response.json())

    async def mcp_proxy(
        self: "Connector" | UuidStr,
        *,
        method: str,
        headers: dict | None = None,
        content: bytes | None = None,
        client: PlatformClient | None = None,
    ) -> AsyncIterator[MCPProxyResponse]:
        """
        Proxy a streaming request through to the connector's MCP endpoint.

        This allows direct communication with the Model Context Protocol server
        exposed by the connector. The response is streamed to avoid loading
        large responses into memory.

        Args:
            method: HTTP method (GET, POST, etc.)
            headers: Optional HTTP headers to include
            content: Optional request body content
            client: Optional PlatformClient instance

        Yields:
            Response content chunks as bytes
        """
        connector_id = str(self.id) if isinstance(self, Connector) else self
        async with client or get_platform_client() as client:
            url = f"/api/v1/connectors/{connector_id}/mcp"

            # Merge headers - add Content-Type for JSON content if not already set
            request_headers = dict(headers or {})
            if content and "content-type" not in {k.lower() for k in request_headers}:
                request_headers["Content-Type"] = "application/json"

            # Use streaming to support large/long-lived connections
            async with client.stream(
                method=method.upper(),
                url=url,
                headers=request_headers,
                content=content,
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield pydantic.TypeAdapter(MCPProxyResponse).validate_python(
                        {"headers": dict(response.headers), "status_code": response.status_code, "chunk": chunk}
                    )

    @staticmethod
    async def presets(
        *,
        client: PlatformClient | None = None,
    ) -> PaginatedResult["ConnectorPreset"]:
        """
        List all available connector presets.

        Returns:
            A paginated list of ConnectorPreset instances
        """
        async with client or get_platform_client() as client:
            response = await client.get(url="/api/v1/connectors/presets")
            response.raise_for_status()
            return pydantic.TypeAdapter(PaginatedResult[ConnectorPreset]).validate_python(response.json())
