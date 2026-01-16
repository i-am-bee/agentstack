# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import webbrowser
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Literal
from uuid import UUID

import pydantic
from pydantic import AnyUrl

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.platform.common import PaginatedResult
from agentstack_sdk.platform.types import Metadata


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
        *,
        url: AnyUrl | str,
        client_id: str | None = None,
        client_secret: str | None = None,
        metadata: Metadata | None = None,
        match_preset: bool = True,
        client: PlatformClient | None = None,
    ) -> Connector:
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
    ) -> PaginatedResult[Connector]:
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
        self: Connector | UUID,
        *,
        client: PlatformClient | None = None,
    ) -> Connector:
        """
        Read a specific connector by ID.
        """
        connector_id = str(self if isinstance(self, UUID) else self.id)
        async with client or get_platform_client() as client:
            response = await client.get(url=f"/api/v1/connectors/{connector_id}")
            response.raise_for_status()
            return pydantic.TypeAdapter(Connector).validate_python(response.json())

    async def delete(
        self: Connector | UUID,
        *,
        client: PlatformClient | None = None,
    ) -> None:
        """
        Delete a connector.

        Args:
            client: Optional PlatformClient instance
        """
        connector_id = str(self if isinstance(self, UUID) else self.id)
        async with client or get_platform_client() as client:
            response = await client.delete(url=f"/api/v1/connectors/{connector_id}")
            response.raise_for_status()

    async def refresh(
        self: Connector | UUID,
        *,
        client: PlatformClient | None = None,
    ) -> Connector:
        """
        This is just a syntactic sugar for calling Connector.get().
        """
        async with client or get_platform_client() as client:
            return await Connector.get(self, client=client)

    async def wait_for_connection(
        self: Connector | UUID,
        *,
        poll_interval: int = 1,
        client: PlatformClient | None = None,
    ) -> Connector:
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
                while connector.state != ConnectorState.connected:
                    await asyncio.sleep(poll_interval)
                    connector = await connector.refresh(client=client)
            return connector

    async def connect(
        self: Connector | UUID,
        *,
        redirect_url: AnyUrl | str | None = None,
        access_token: str | None = None,
        client: PlatformClient | None = None,
    ) -> Connector:
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
        connector_id = str(self if isinstance(self, UUID) else self.id)
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
        self: Connector | UUID,
        *,
        client: PlatformClient | None = None,
    ) -> Connector:
        """
        Disconnect a connector.

        Args:
            client: Optional PlatformClient instance

        Returns:
            The updated Connector instance
        """
        connector_id = str(self if isinstance(self, UUID) else self.id)
        async with client or get_platform_client() as client:
            response = await client.post(url=f"/api/v1/connectors/{connector_id}/disconnect")
            response.raise_for_status()
            return pydantic.TypeAdapter(Connector).validate_python(response.json())

    async def mcp_proxy(
        self: Connector | UUID,
        *,
        method: str,
        headers: dict | None = None,
        content: bytes | None = None,
        client: PlatformClient | None = None,
    ) -> AsyncIterator[bytes]:
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
        connector_id = str(self if isinstance(self, UUID) else self.id)
        async with client or get_platform_client() as client:
            url = f"/api/v1/connectors/{connector_id}/mcp"

            # Use streaming to support large/long-lived connections
            response_stream = client.stream(
                method=method.upper(),
                url=url,
                headers=headers,
                content=content,
            )
            async with response_stream as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk

    @staticmethod
    async def presets(
        *,
        client: PlatformClient | None = None,
    ) -> PaginatedResult[ConnectorPreset]:
        """
        List all available connector presets.

        Returns:
            A paginated list of ConnectorPreset instances
        """
        async with client or get_platform_client() as client:
            response = await client.get(url="/api/v1/connectors/presets")
            response.raise_for_status()
            return pydantic.TypeAdapter(PaginatedResult[ConnectorPreset]).validate_python(response.json())
