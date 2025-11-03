# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import html
import logging
from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import UUID

import httpx
from async_lru import alru_cache
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata, get_well_known_url
from fastapi import status
from fastapi.responses import HTMLResponse, RedirectResponse
from kink import inject
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import AnyUrl, BaseModel

from agentstack_server.configuration import Configuration, ConnectorPreset
from agentstack_server.domain.models.common import Metadata
from agentstack_server.domain.models.connector import (
    Authorization,
    AuthorizationCodeFlow,
    Connector,
    ConnectorState,
    Token,
)
from agentstack_server.domain.models.user import User
from agentstack_server.exceptions import EntityNotFoundError, PlatformError
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ConnectorService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration):
        self._uow = uow
        self._configuration = configuration

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

        preset = self._find_preset(url=url) if match_preset else None
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
            await self._revoke_auth_token(connector=connector)
            await uow.connectors.delete(connector_id=connector_id, user_id=user.id if user else None)
            await uow.commit()

    async def list_connectors(self, *, user: User | None = None) -> list[Connector]:
        async with self._uow() as uow:
            return [c async for c in uow.connectors.list(user_id=user.id if user else None)]

    async def connect_connector(
        self, *, connector_id: UUID, callback_uri: str, redirect_url: AnyUrl | None = None, user: User | None = None
    ) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        try:
            await self.probe_connector(connector=connector)
            connector.state = ConnectorState.connected
            connector.disconnect_reason = None
        except Exception as err:
            if isinstance(err, httpx.HTTPStatusError):
                if err.response.status_code == status.HTTP_401_UNAUTHORIZED:
                    await self._bootstrap_auth(
                        connector=connector, callback_url=callback_uri, redirect_url=redirect_url
                    )
                    connector.state = ConnectorState.auth_required
                else:
                    raise PlatformError(
                        (await err.response.aread()).decode(err.response.encoding or "utf-8"),
                        status_code=status.HTTP_502_BAD_GATEWAY,
                    ) from err
            elif isinstance(err, httpx.RequestError):
                raise PlatformError(
                    "Connector must be in connected or auth_required state",
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                ) from err
            else:
                logger.error("Connector failed", exc_info=True)
                raise PlatformError("Connection has failed") from err

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def disconnect_connector(self, *, connector_id: UUID, user: User | None = None) -> Connector:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state not in (ConnectorState.connected, ConnectorState.auth_required):
            raise PlatformError(
                "Connector must be in connected or auth_required state", status_code=status.HTTP_400_BAD_REQUEST
            )

        await self._revoke_auth_token(connector=connector)

        connector.state = ConnectorState.disconnected

        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()
        return connector

    async def oauth_callback(self, *, callback_url: str, state: str, error: str | None, error_description: str | None):
        redirect_url = None
        try:
            async with self._uow() as uow:
                connector = await uow.connectors.get_by_auth(auth_state=state)

            assert connector.auth is not None
            assert connector.auth.flow is not None
            assert connector.auth.flow.type == "code"

            redirect_url = connector.auth.flow.redirect_url

            if error:
                return self._create_callback_response(
                    redirect_url=redirect_url, error=error, error_description=error_description
                )

            if connector.state not in (ConnectorState.auth_required):
                return self._create_callback_response(
                    redirect_url=redirect_url,
                    error="invalid_request",
                    error_description="Connector must be in auth_required state.",
                )

            async with self._create_oauth_client(connector=connector) as client:
                auth_metadata = await self._discover_auth_metadata(connector=connector)
                if not auth_metadata:
                    raise RuntimeError("Authorization server no longer contains necessary metadata")
                token = await client.fetch_token(
                    auth_metadata.get("token_endpoint"),
                    authorization_response=callback_url,
                    code_verifier=connector.auth.flow.code_verifier,
                )
                connector.auth.token = Token.model_validate(token)
                connector.auth.flow = None
            try:
                await self.probe_connector(connector=connector)
                connector.state = ConnectorState.connected
            except Exception as err:
                logger.error("Failed to probe resource with a valid token", exc_info=True)
                connector.state = ConnectorState.disconnected
                connector.disconnect_reason = str(err)

            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

            return self._create_callback_response(redirect_url=redirect_url)
        except EntityNotFoundError:
            return self._create_callback_response(
                redirect_url=redirect_url,
                error="invalid_request",
                error_description="Invalid or expired login attempt.",
            )
        except Exception:
            logger.error("oAuth callback failed", exc_info=True)
            return self._create_callback_response(
                redirect_url=redirect_url,
                error="server_error",
                error_description="An internal error has occurred. Please try again later.",
            )

    def _create_callback_response(
        self, *, redirect_url: AnyUrl | None, error: str | None = None, error_description: str | None = None
    ):
        if redirect_url:
            if error:
                parsed = urlparse(str(redirect_url))
                query_params = parse_qs(parsed.query)
                query_params["error"] = [error]
                if error_description:
                    query_params["error_description"] = [error_description]
                modified_url = urlunparse(parsed._replace(query=urlencode(query_params, doseq=True)))
                redirect_url = AnyUrl(modified_url)
            return RedirectResponse(str(redirect_url))
        else:
            return HTMLResponse(
                _render_success() if not error else _render_failure(error, error_description=error_description)
            )

    async def refresh_connector(self, *, connector_id: UUID, user: User | None = None) -> None:
        async with self._uow() as uow:
            connector = await uow.connectors.get(connector_id=connector_id, user_id=user.id if user else None)

        if connector.state != ConnectorState.connected:
            return

        try:
            await self.probe_connector(connector=connector)
        except Exception as err:
            connector.state = ConnectorState.disconnected
            connector.disconnect_reason = str(err)
        finally:
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

    async def list_presets(self) -> list[ConnectorPreset]:
        return self._configuration.connector.presets

    def _find_preset(self, *, url: AnyUrl) -> ConnectorPreset | None:
        for preset in self._configuration.connector.presets:
            if preset.url == url:
                return preset
        return None

    async def _bootstrap_auth(self, *, connector: Connector, callback_url: str, redirect_url: AnyUrl | None) -> None:
        auth_metadata = await self._discover_auth_metadata(connector=connector)
        if not auth_metadata:
            raise RuntimeError("Not authorization server found for the connector")

        if not connector.auth:
            connector.auth = Authorization()

        await self._revoke_auth_token(connector=connector)
        code_verifier = token_urlsafe(64)

        await self._ensure_oauth_client_registered(connector=connector, redirect_uri=callback_url)

        async with self._create_oauth_client(connector=connector) as client:
            uri, state = client.create_authorization_url(
                auth_metadata.get("authorization_endpoint"),
                code_verifier=code_verifier,
                redirect_uri=callback_url,
            )
            connector.auth.flow = AuthorizationCodeFlow(
                authorization_endpoint=uri, state=state, code_verifier=code_verifier, redirect_url=redirect_url
            )

    async def _revoke_auth_token(self, *, connector: Connector) -> None:
        if not connector.auth or not connector.auth.token:
            return

        if connector.auth.token:
            try:
                async with self._create_oauth_client(connector=connector) as client:
                    auth_metadata = await self._discover_auth_metadata(connector=connector)
                    if not auth_metadata:
                        raise RuntimeError("Authorization server no longer contains necessary metadata")
                    revoke_endpoint = auth_metadata.get("revocation_endpoint")
                    if not isinstance(revoke_endpoint, str):
                        raise RuntimeError("Authorization server does not support token revocation")
                    await client.revoke_token(revoke_endpoint, token=connector.auth.token.access_token)
            except Exception:
                logger.warning("Token revocation failed", exc_info=True)

            connector.auth.token = None
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

    def _create_client(
        self, *, connector: Connector, headers: dict[str, str] | None = None, timeout: int | None = None
    ) -> httpx.AsyncClient:
        if not connector.auth or not connector.auth.token:
            return httpx.AsyncClient(base_url=str(connector.url), headers=headers, timeout=timeout)
        else:
            return self._create_oauth_client(connector=connector)

    def _create_oauth_client(
        self, *, connector: Connector, headers: dict[str, str] | None = None, timeout: int | None = None
    ) -> AsyncOAuth2Client:
        if not connector.auth:
            raise RuntimeError("Connector does not support auth")

        async def update_token(token, refresh_token=None, access_token=None):
            if not connector.auth:
                raise RuntimeError("Authorization has been removed from the connector")
            connector.auth.token = Token.model_validate(token)
            async with self._uow() as uow:
                await uow.connectors.update(connector=connector)
                await uow.commit()

        return AsyncOAuth2Client(
            client_id=connector.auth.client_id,
            client_secret=connector.auth.client_secret,
            token=connector.auth.token.model_dump() if connector.auth.token else None,
            update_token=update_token,
            code_challenge_method="S256",
            headers=headers,
            timeout=timeout,
        )

    async def _discover_auth_metadata(self, *, connector: Connector) -> AuthorizationServerMetadata | None:
        resource_metadata = await _discover_resource_metadata(str(connector.url))
        if not resource_metadata or not resource_metadata.authorization_servers:
            return None
        auth_metadata = await _discover_auth_metadata(resource_metadata.authorization_servers[0])
        return auth_metadata

    async def _ensure_oauth_client_registered(self, *, connector: Connector, redirect_uri: str) -> Connector:
        if not connector.auth:
            raise RuntimeError("Authoriztion hasn't been activated for connector")
        if not connector.auth.client_id:
            registration_response = await _register_client(str(connector.url), redirect_uri=redirect_uri)
            async with self._uow() as uow:
                connector.auth.client_id = registration_response.client_id
                connector.auth.client_secret = registration_response.client_secret
                await uow.connectors.update(connector=connector)
                await uow.commit()
        return connector

    async def probe_connector(self, *, connector: Connector):
        def client_factory(headers=None, timeout=None, auth=None):
            assert auth is None
            return self._create_client(connector=connector, headers=headers, timeout=timeout)

        try:
            async with (
                streamablehttp_client(str(connector.url), httpx_client_factory=client_factory) as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
        except ExceptionGroup as excgroup:
            if len(excgroup.exceptions) == 1:
                raise excgroup.exceptions[0] from excgroup
            raise excgroup


@alru_cache(ttl=timedelta(days=1).seconds)
async def _register_client(resource_server_url: str, *, redirect_uri: str) -> _ClientRegistrationResponse:
    resource_metadata = await _discover_resource_metadata(resource_server_url)
    if not resource_metadata or not resource_metadata.authorization_servers:
        raise RuntimeError("Resource server metadata not found")
    auth_metadata = await _discover_auth_metadata(resource_metadata.authorization_servers[0])
    if not auth_metadata:
        raise RuntimeError("Authorization server metadata not found")
    registration_endpoint = auth_metadata.get("registration_endpoint")
    if not isinstance(registration_endpoint, str):
        raise RuntimeError("Authorization server does not support dynamic client registration")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            str(registration_endpoint), json={"client_name": "Agent Stack", "redirect_uris": [redirect_uri]}
        )
        response.raise_for_status()
        registration_response = _ClientRegistrationResponse.model_validate(response.json())
        return registration_response


@alru_cache(ttl=timedelta(minutes=10).seconds)
async def _discover_auth_metadata(authorization_server_url: str) -> AuthorizationServerMetadata | None:
    url = get_well_known_url(authorization_server_url, external=True)
    async with httpx.AsyncClient(headers={"Accept": "application/json"}, follow_redirects=True) as client:
        response = await client.get(url)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        response.raise_for_status()
        metadata = AuthorizationServerMetadata(response.json())
        metadata.validate()
        return metadata


@alru_cache(ttl=timedelta(minutes=10).seconds)
async def _discover_resource_metadata(resource_server_url: str) -> _ResourceServerMetadata | None:
    # RFC9728 hasn't been implemented yet in authlib
    # Reusing util from RFC8414
    url = get_well_known_url(resource_server_url, external=True, suffix="oauth-protected-resource")
    async with httpx.AsyncClient(
        headers={"Accept": "application/json"},
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None
        response.raise_for_status()
        return _ResourceServerMetadata.model_validate(response.json())


def _render_success():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Stack</title>
  <style>
    body { font-family: system-ui, sans-serif; text-align: center; margin-top: 5rem; }
  </style>
</head>
<body>
  <h1 id="msg">Authorization Successful</h1>
  <p id="detail">You can now close this window and return to your application.</p>

  <script>
    // Auto-close after 8 seconds (best effort)
    setTimeout(() => window.close(), 8000);
  </script>
</body>
</html>"""


def _render_failure(error: str, error_description: str | None):
    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Stack</title>
  <style>
    body { font-family: system-ui, sans-serif; text-align: center; margin-top: 5rem; }
  </style>
</head>
<body>
  <h1 id="msg">Authorization Failed</h1>
  <p id="detail">"""
        + html.escape(error_description or error)
        + """</p>
</body>
</html>"""
    )


class _ResourceServerMetadata(BaseModel):
    authorization_servers: list[str]


class _ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: str | None = None
