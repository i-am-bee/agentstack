# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from uuid import UUID

import httpx
from authlib.oauth2 import OAuth2Error
from fastapi import Request, status
from fastapi.responses import StreamingResponse
from httpx import ConnectError, ReadError, RemoteProtocolError, TimeoutException
from kink import inject
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import AnyUrl

from agentstack_server.configuration import Configuration, ConnectorPreset
from agentstack_server.domain.models.common import Metadata
from agentstack_server.domain.models.connector import (
    Authorization,
    Connector,
    ConnectorState,
    Token,
)
from agentstack_server.domain.models.user import User
from agentstack_server.exceptions import PlatformError
from agentstack_server.service_layer.services.external_mcp_service import ExternalMcpService
from agentstack_server.service_layer.services.managed_mcp_service import ManagedMcpService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ConnectorService:
    def __init__(
        self,
        uow: IUnitOfWorkFactory,
        configuration: Configuration,
        managed_mcp: ManagedMcpService,
        external_mcp: ExternalMcpService,
    ):
        self._uow = uow
        self._configuration = configuration
        self._proxy_client = httpx.AsyncClient(timeout=None)
        self._managed_mcp = managed_mcp
        self._external_mcp = external_mcp

    async def create_connector(
        self,
        *,
        user: User,
        url: AnyUrl,
        client_id: str | None,
        client_secret: str | None,
        metadata: Metadata | None,
        match_preset: bool = True,
    ) -> Connector:
        if client_secret and not client_id:
            raise PlatformError(
                "client_id must be present when client_secret is specified", status_code=status.HTTP_400_BAD_REQUEST
            )

        preset = (
            next((p for p in self._configuration.connector.presets if str(p.url) == str(url)), None)
            if match_preset or url.scheme == "mcp+stdio"
            else None
        )
        if url.scheme not in ("http", "https", "mcp+stdio"):
            raise PlatformError("Connector URL has an unsupported scheme", status_code=status.HTTP_400_BAD_REQUEST)
        if not preset and url.scheme == "mcp+stdio":
            raise PlatformError(
                "Connector URL has mcp+stdio scheme but does not match a known connector preset",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if preset:
            if not client_id:
                client_id = preset.client_id
                client_secret = preset.client_secret
            metadata = metadata or preset.metadata

        connector = Connector(
            url=url,
            created_by=user.id,
            auth=Authorization(client_id=client_id, client_secret=client_secret) if client_id else None,
            metadata=metadata,
        )
        async with self._uow() as uow:
            await uow.connectors.create(connector=connector)
            await uow.commit()
        return connector

    async def read_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            return await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

    async def delete_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)
            await self._external_mcp.revoke_token(connector=connector)
            await uow.connectors.delete(connector_id=connector_id, user_id=user.id if user else None)
            await uow.commit()

    async def list_connectors(self, *, user: User | None = None) -> list[Connector]:
        async with self._uow() as uow:
            return [c async for c in uow.connectors.list(user_id=user.id if user else None)]

    async def _handle_connection_error(
        self,
        err: Exception,
        connector: Connector,
        callback_uri: str,
        redirect_url: AnyUrl | None = None,
    ) -> None:
        """Handle various connection errors and update connector state accordingly."""
        if isinstance(err, OAuth2Error) or (
            isinstance(err, httpx.HTTPStatusError) and err.response.status_code == status.HTTP_401_UNAUTHORIZED
        ):
            await self._external_mcp.bootstrap_auth(
                connector=connector, callback_url=callback_uri, redirect_url=redirect_url
            )
            connector.state = ConnectorState.auth_required
        elif isinstance(err, httpx.HTTPStatusError):
            logger.error("Connector failed", exc_info=True)
            try:
                error = (await err.response.aread()).decode(err.response.encoding or "utf-8")
            except Exception:
                error = "Connector has returned an error"
            raise PlatformError(
                error,
                status_code=status.HTTP_502_BAD_GATEWAY,
            ) from err
        elif isinstance(err, httpx.RequestError):
            logger.error("Connector failed", exc_info=True)
            raise PlatformError(
                "Unable to establish connection with the connector",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ) from err
        else:
            logger.error("Connector failed", exc_info=True)
            raise PlatformError("Connection has failed") from err

    async def connect_connector(
        self,
        *,
        connector_id: UUID,
        callback_uri: str,
        redirect_url: AnyUrl | None = None,
        user: User | None = None,
        access_token: str | None = None,
    ) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)
        if access_token:
            if not connector.auth:
                connector.auth = Authorization()
            connector.auth.token = Token(access_token=access_token, token_type="bearer")

        if self._managed_mcp.is_managed(connector=connector) and (preset := self._find_preset(url=connector.url)):
            await self._managed_mcp.deploy(connector=connector, preset=preset)

        try:
            await self.probe_connector(connector=connector)
            connector.state = ConnectorState.connected
            connector.disconnect_reason = None
        except Exception as err:
            await self._handle_connection_error(err, connector, callback_uri, redirect_url)

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def disconnect_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.connected, ConnectorState.disconnected, ConnectorState.auth_required):
            raise PlatformError(
                "Connector must be in connected, disconnected or auth_required state",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        await self._external_mcp.revoke_token(connector=connector)

        if connector.auth:
            connector.auth.flow = None
        connector.state = ConnectorState.disconnected
        connector.disconnect_reason = "Client request"

        if self._managed_mcp.is_managed(connector=connector):
            await self._managed_mcp.undeploy(connector=connector)

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def refresh_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.connected, ConnectorState.disconnected):
            return

        try:
            await self.probe_connector(connector=connector)
            connector.state = ConnectorState.connected
            connector.disconnect_reason = None
        except Exception as err:
            if isinstance(err, httpx.HTTPStatusError) and err.response.status_code == status.HTTP_401_UNAUTHORIZED:
                await self._external_mcp.revoke_token(connector=connector)
                if connector.auth:
                    connector.auth.flow = None
            connector.state = ConnectorState.disconnected
            connector.disconnect_reason = str(err)
        finally:
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

    async def list_presets(self) -> list[ConnectorPreset]:
        return self._configuration.connector.presets

    def _find_preset(self, *, url: AnyUrl) -> ConnectorPreset | None:
        return next((p for p in self._configuration.connector.presets if str(p.url) == str(url)), None)

    async def probe_connector(self, *, connector: Connector):
        def client_factory(headers=None, timeout=None, auth=None):
            assert auth is None
            return self._external_mcp.create_http_client(connector=connector, headers=headers, timeout=timeout)

        # For managed MCP servers, retry if connection fails as service might not be immediately ready
        is_managed = self._managed_mcp.is_managed(connector=connector)
        max_retries = 5 if is_managed else 1
        retry_delay = 2.0

        last_error = None
        for attempt in range(max_retries):
            try:
                async with (
                    streamablehttp_client(
                        (
                            f"{self._managed_mcp.get_service_url(connector=connector)}/mcp"
                            if is_managed
                            else str(connector.url)
                        ),
                        httpx_client_factory=client_factory,
                    ) as (read, write, _),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    return  # Success, exit retry loop
            except ExceptionGroup as excgroup:
                last_error = excgroup.exceptions[0] if len(excgroup.exceptions) == 1 else excgroup

                # Check if we should retry (only for managed MCP servers on connection errors)
                should_retry = (
                    attempt < max_retries - 1
                    and is_managed
                    and isinstance(last_error, (ReadError, ConnectError, RemoteProtocolError, TimeoutException))
                )

                if should_retry:
                    logger.warning(
                        f"Probe attempt {attempt + 1}/{max_retries} failed for managed MCP server {connector.url}, retrying in {retry_delay}s: {last_error}"
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                # Not retrying, log and raise the error
                logger.warning(f"Probe failed for MCP server {connector.url}: {last_error}")
                if len(excgroup.exceptions) == 1:
                    raise last_error from excgroup
                raise excgroup from None

    async def mcp_proxy(self, *, connector_id: UUID, request: Request, user: User | None = None):
        connector = await self.read_connector(connector_id=connector_id, user=user)

        auth_headers = {}
        if (
            connector.auth
            and connector.state == ConnectorState.connected
            and connector.auth.token
            and connector.auth.token.token_type == "bearer"
        ):
            auth_headers["authorization"] = f"Bearer {connector.auth.token.access_token}"

        exit_stack = AsyncExitStack()
        try:
            response = await exit_stack.enter_async_context(
                self._proxy_client.stream(
                    request.method,
                    (
                        f"{self._managed_mcp.get_service_url(connector=connector)}/mcp"
                        if self._managed_mcp.is_managed(connector=connector)
                        else str(connector.url)
                    ),
                    headers={
                        key: request.headers[key]
                        for key in ["accept", "content-type", "mcp-protocol-version", "mcp-session-id", "last-event-id"]
                        if key in request.headers
                    }
                    | auth_headers,
                    content=request.stream(),
                )
            )

            async def stream_fn():
                try:
                    async for chunk in response.aiter_bytes():
                        yield chunk
                finally:
                    await exit_stack.pop_all().aclose()

            return StreamingResponse(stream_fn(), status_code=response.status_code, headers=response.headers)
        except BaseException:
            await exit_stack.pop_all().aclose()
            raise
