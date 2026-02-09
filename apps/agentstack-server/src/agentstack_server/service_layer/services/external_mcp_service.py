# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta
from secrets import token_urlsafe
from types import CoroutineType
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
from async_lru import alru_cache
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata, get_well_known_url
from fastapi import status
from fastapi.responses import HTMLResponse, RedirectResponse
from kink import inject
from pydantic import AnyUrl, BaseModel

from agentstack_server.domain.models.connector import (
    Authorization,
    AuthorizationCodeFlow,
    Connector,
    ConnectorState,
    Token,
)
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ExternalMcpService:
    def __init__(self, uow: IUnitOfWorkFactory):
        self._uow = uow

    async def bootstrap_auth(self, *, connector: Connector, callback_url: str, redirect_url: AnyUrl | None) -> None:
        if not (auth_metadata := await self._discover_auth_metadata(connector=connector)):
            raise RuntimeError("No authorization server found for the connector")

        if not connector.auth:
            connector.auth = Authorization()

        await self.revoke_token(connector=connector)
        await self._ensure_client_registered(connector=connector, redirect_uri=callback_url)

        async with self._create_client(connector=connector) as client:
            uri, state = client.create_authorization_url(
                auth_metadata.get("authorization_endpoint"),
                code_verifier=(code_verifier := token_urlsafe(64)),
                redirect_uri=callback_url,
            )
            connector.auth.flow = AuthorizationCodeFlow(
                authorization_endpoint=uri,
                state=state,
                code_verifier=code_verifier,
                redirect_uri=callback_url,
                client_redirect_uri=redirect_url,
            )

    async def revoke_token(self, *, connector: Connector) -> None:
        if not connector.auth or not connector.auth.token:
            return

        try:
            async with self._create_client(connector=connector) as client:
                if not (auth_metadata := await self._discover_auth_metadata(connector=connector)):
                    raise RuntimeError("Authorization server no longer contains necessary metadata")
                if not isinstance(revoke_endpoint := auth_metadata.get("revocation_endpoint"), str):
                    raise RuntimeError("Authorization server does not support token revocation")
                await client.revoke_token(revoke_endpoint, token=connector.auth.token.access_token)
        except Exception:
            logger.warning("Token revocation failed", exc_info=True)

        connector.auth.token = None
        connector.auth.token_endpoint = None
        async with self._uow() as uow:
            await uow.connectors.update(connector=connector)
            await uow.commit()

    def create_http_client(
        self, *, connector: Connector, headers: dict[str, str] | None = None, timeout: int | None = None
    ) -> httpx.AsyncClient:
        if not connector.auth or not connector.auth.token:
            return httpx.AsyncClient(
                headers=headers,
                timeout=timeout or 30,
                base_url=str(connector.url),
            )
        else:
            return self._create_client(connector=connector, headers=headers, timeout=timeout)

    def _create_client(
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
            leeway=60,
            token_endpoint=str(connector.auth.token_endpoint),
        )

    async def _discover_auth_metadata(self, *, connector: Connector) -> AuthorizationServerMetadata | None:
        resource_metadata = await _discover_resource_metadata(str(connector.url))
        if not resource_metadata or not resource_metadata.authorization_servers:
            return None
        return await _discover_auth_metadata(resource_metadata.authorization_servers[0])

    async def _ensure_client_registered(self, *, connector: Connector, redirect_uri: str) -> None:
        if not connector.auth:
            raise RuntimeError("Authoriztion hasn't been activated for connector")
        if not connector.auth.client_id:
            registration_response = await _register_client(str(connector.url), redirect_uri=redirect_uri)
            async with self._uow() as uow:
                connector.auth.client_id = registration_response.client_id
                connector.auth.client_secret = registration_response.client_secret
                await uow.connectors.update(connector=connector)
                await uow.commit()

    async def fetch_token_from_callback(self, *, connector: Connector, callback_url: str) -> Token:
        async with self._create_client(connector=connector) as client:
            if not (auth_metadata := await self._discover_auth_metadata(connector=connector)):
                raise RuntimeError("Authorization server no longer contains necessary metadata")
            if not (token_endpoint := auth_metadata.get("token_endpoint")):
                raise RuntimeError("Authorization server has no token endpoint in metadata")
            assert connector.auth and connector.auth.flow
            token = Token.model_validate(
                await client.fetch_token(
                    token_endpoint,
                    authorization_response=callback_url,
                    code_verifier=connector.auth.flow.code_verifier,
                    redirect_uri=connector.auth.flow.redirect_uri,
                )
            )
            connector.auth.token = token
            connector.auth.token_endpoint = AnyUrl(str(token_endpoint))
            connector.auth.flow = None
            return token

    async def oauth_callback(
        self,
        *,
        callback_url: str,
        state: str,
        error: str | None,
        error_description: str | None,
        probe_fn: Callable[[Connector], CoroutineType[Any, Any, None]],
    ):
        redirect_url = None
        try:
            async with self._uow() as uow:
                connector = await uow.connectors.get_by_auth(auth_state=state)

            assert connector.auth is not None
            assert connector.auth.flow is not None
            assert connector.auth.flow.type == "code"

            redirect_url = connector.auth.flow.client_redirect_uri

            if error:
                return self._create_callback_response(
                    redirect_url=redirect_url, error=error, error_description=error_description
                )

            if connector.state not in (ConnectorState.auth_required,):
                return self._create_callback_response(
                    redirect_url=redirect_url,
                    error="invalid_request",
                    error_description="Connector must be in auth_required state.",
                )

            await self.fetch_token_from_callback(connector=connector, callback_url=callback_url)
            try:
                await probe_fn(connector)
                connector.transition(state=ConnectorState.connected)
            except Exception as err:
                logger.error("Failed to probe resource with a valid token", exc_info=True)
                connector.transition(
                    state=ConnectorState.disconnected, disconnect_reason=str(err), disconnect_permanent=True
                )

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
                redirect_url = AnyUrl(
                    # pyrefly: ignore[bad-argument-type]
                    urlunparse(parsed._replace(query=urlencode(query_params, doseq=True)))
                )
            return RedirectResponse(str(redirect_url))
        return HTMLResponse(_render_success() if not error else _render_failure(error, error_description))


@alru_cache(ttl=timedelta(days=1).seconds)
async def _register_client(resource_server_url: str, *, redirect_uri: str) -> _ClientRegistrationResponse:
    if (
        not (resource_metadata := await _discover_resource_metadata(resource_server_url))
        or not resource_metadata.authorization_servers
    ):
        raise RuntimeError("Resource server metadata not found")
    if not (auth_metadata := await _discover_auth_metadata(resource_metadata.authorization_servers[0])):
        raise RuntimeError("Authorization server metadata not found")
    if not isinstance(registration_endpoint := auth_metadata.get("registration_endpoint"), str):
        raise RuntimeError("Authorization server does not support dynamic client registration")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            str(registration_endpoint),
            json={"client_name": "Agent Stack", "redirect_uris": [redirect_uri]},
        )
        response.raise_for_status()
        return _ClientRegistrationResponse.model_validate(response.json())


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
async def _discover_resource_metadata(resource_url: str) -> _ResourceServerMetadata | None:
    parsed = urlparse(resource_url)
    path_url = get_well_known_url(resource_url, external=True, suffix="oauth-protected-resource")
    root_url = get_well_known_url(
        f"{parsed.scheme}://{parsed.netloc}", external=True, suffix="oauth-protected-resource"
    )
    exceptions = []
    async with httpx.AsyncClient(headers={"Accept": "application/json"}, follow_redirects=True) as client:
        for url in [path_url] if path_url == root_url else [path_url, root_url]:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return _ResourceServerMetadata.model_validate(response.json())
            except Exception as exc:
                exceptions.append(exc)
    logger.warning(
        "Resource metadata discovery failed",
        exc_info=ExceptionGroup(f"Unable to discover metadata for resource {resource_url}", exceptions),
    )
    return None


class _ResourceServerMetadata(BaseModel):
    authorization_servers: list[str]


class _ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: str | None = None


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
    import html

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
