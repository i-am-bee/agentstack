# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import pathlib
import time
import typing
from collections import defaultdict
from typing import Any

import httpx
from authlib.common.errors import AuthlibBaseError
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc6749.errors import InvalidGrantError, OAuth2Error
from pydantic import BaseModel, Field

TOKEN_EXPIRY_LEEWAY = 60  # seconds


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    expires_at: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


class AuthServer(BaseModel):
    client_id: str = "df82a687-d647-4247-838b-7080d7d83f6c"  # Backwards compatibility default
    client_secret: str | None = None
    token: AuthToken | None = None
    registration_token: str | None = None


class Server(BaseModel):
    authorization_servers: dict[str, AuthServer] = Field(default_factory=dict)


class Auth(BaseModel):
    version: typing.Literal[1] = 1
    servers: defaultdict[str, typing.Annotated[Server, Field(default_factory=Server)]] = Field(
        default_factory=lambda: defaultdict(Server)
    )
    active_server: str | None = None
    active_auth_server: str | None = None


@typing.final
class AuthManager:
    def __init__(self, config_path: pathlib.Path):
        self._auth_path = config_path
        self._auth = self._load()
        self._oidc_cache: dict[str, dict[str, Any]] = {}

    def _load(self) -> Auth:
        if not self._auth_path.exists():
            return Auth()
        return Auth.model_validate_json(self._auth_path.read_bytes())

    def _save(self) -> None:
        self._auth_path.write_text(self._auth.model_dump_json(indent=2))

    async def _get_oidc_metadata(self, auth_server: str) -> dict[str, Any]:
        """Fetch and cache OIDC metadata."""
        if auth_server in self._oidc_cache:
            return self._oidc_cache[auth_server]

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{auth_server}/.well-known/openid-configuration")
                resp.raise_for_status()
                metadata = resp.json()
                self._oidc_cache[auth_server] = metadata
                return metadata
            except Exception as e:
                raise RuntimeError(f"OIDC discovery failed: {e}") from e

    def _create_token_update_callback(self, server: str, auth_server: str):
        """Create a callback that saves tokens when they're refreshed."""

        def update_token(token: dict[str, Any]):
            # Authlib calls this automatically when tokens are refreshed
            # kwargs may include refresh_token and access_token but we don't need them
            auth_config = self._auth.servers[server].authorization_servers[auth_server]
            self.save_auth_info(
                server=server,
                auth_server=auth_server,
                client_id=auth_config.client_id,
                client_secret=auth_config.client_secret,
                token=token,
                registration_token=auth_config.registration_token,
            )

        return update_token

    async def _get_oauth_client(self, server: str, auth_server: str) -> AsyncOAuth2Client:
        """Create an OAuth2 client configured with current credentials."""
        auth_config = self._auth.servers[server].authorization_servers[auth_server]

        if not auth_config or not auth_config.token:
            raise ValueError(f"No token found for {auth_server}")

        metadata = await self._get_oidc_metadata(auth_server)

        # Convert AuthToken to dict format authlib expects
        token_dict = auth_config.token.model_dump(exclude_none=True)

        client = AsyncOAuth2Client(
            client_id=auth_config.client_id,
            client_secret=auth_config.client_secret,
            token_endpoint=metadata["token_endpoint"],
            token=token_dict,
            scope=token_dict.get("scope"),
            update_token=self._create_token_update_callback(server, auth_server),
        )

        return client

    def save_auth_info(
        self,
        server: str,
        auth_server: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token: dict[str, Any] | None = None,
        registration_token: str | None = None,
    ) -> None:
        if auth_server is not None and client_id is not None and token is not None:
            if token["access_token"] and token.get("expires_in") is not None:
                usetimestamp = int(time.time()) + int(token["expires_in"])
                token["expires_at"] = usetimestamp
            self._auth.servers[server].authorization_servers[auth_server] = AuthServer(
                client_id=client_id,
                client_secret=client_secret,
                token=AuthToken(**token),
                registration_token=registration_token,
            )
        else:
            self._auth.servers[server]  # touch
        self._save()

    async def exchange_refresh_token(self, auth_server: str, token: AuthToken) -> dict[str, Any] | None:
        """
        Exchange a refresh token for a new access token using authlib.

        Raises:
            InvalidGrantError: If the refresh token is invalid or expired (4xx auth errors)
            OAuth2Error: For other OAuth2 protocol errors
            RuntimeError: For network errors or OIDC discovery failures
        """
        if not self._auth.active_server:
            raise ValueError("No active server configured")

        try:
            metadata = await self._get_oidc_metadata(auth_server)
            token_endpoint = metadata["token_endpoint"]

            async with await self._get_oauth_client(self._auth.active_server, auth_server) as client:
                # Authlib's fetch_token with refresh_token grant automatically handles the refresh
                # and calls update_token callback to save the new token
                new_token = await client.fetch_token(
                    url=token_endpoint,
                    grant_type="refresh_token",
                    refresh_token=token.refresh_token,
                )
                return new_token
        except InvalidGrantError as e:
            # 400-level OAuth errors: invalid/expired refresh token
            raise InvalidGrantError(
                description=f"Token refresh failed - invalid or expired refresh token: {e.description}"
            ) from e
        except OAuth2Error as e:
            # Other OAuth2 protocol errors
            raise OAuth2Error(description=f"OAuth2 error during token refresh: {e.description}") from e
        except AuthlibBaseError as e:
            # Other authlib errors
            raise RuntimeError(f"Token refresh failed: {e}") from e
        except Exception as e:
            # Network errors, OIDC discovery failures, etc.
            raise RuntimeError(f"Failed to refresh token: {e}") from e

    async def load_auth_token(self) -> str | None:
        """
        Load and refresh auth token if needed using authlib.

        Returns:
            Access token string, or None if no auth configured

        Raises:
            InvalidGrantError: If token is expired and refresh fails due to auth issues (4xx)
            OAuth2Error: For other OAuth2 protocol errors
            RuntimeError: For network or other errors
        """
        active_res = self._auth.active_server
        active_auth_server = self._auth.active_auth_server
        if not active_res or not active_auth_server:
            return None
        server = self._auth.servers.get(active_res)
        if not server:
            return None
        auth_server = server.authorization_servers.get(active_auth_server)
        if not auth_server or not auth_server.token:
            return None

        if (auth_server.token.expires_at or 0) - TOKEN_EXPIRY_LEEWAY < time.time():
            # Token expired, try to refresh - this may raise TokenRefreshError
            new_token = await self.exchange_refresh_token(active_auth_server, auth_server.token)
            if new_token:
                return new_token["access_token"]
            return None

        return auth_server.token.access_token

    async def deregister_client(self, auth_server: str, client_id: str | None, registration_token: str | None) -> None:
        """Deregister a dynamically registered OAuth2 client."""
        if not client_id or not registration_token:
            return  # Nothing to deregister

        try:
            metadata = await self._get_oidc_metadata(auth_server)
            registration_endpoint = metadata.get("registration_endpoint")

            if not registration_endpoint:
                raise RuntimeError("Registration endpoint not found in OIDC metadata")

            async with AsyncOAuth2Client() as client:
                headers = {"Authorization": f"Bearer {registration_token}"}
                resp = await client.delete(f"{registration_endpoint}/{client_id}", headers=headers)
                resp.raise_for_status()

        except Exception as e:
            raise RuntimeError(f"Dynamic client de-registration failed: {e}") from e

    async def clear_auth_token(self, all: bool = False) -> None:
        if all:
            for server in self._auth.servers:
                for auth_server in self._auth.servers[server].authorization_servers:
                    auth_config = self._auth.servers[server].authorization_servers[auth_server]
                    await self.deregister_client(
                        auth_server,
                        auth_config.client_id,
                        auth_config.registration_token,
                    )

            self._auth.servers = defaultdict(Server)
        else:
            if self._auth.active_server and self._auth.active_auth_server:
                auth_config = self._auth.servers[self._auth.active_server].authorization_servers[
                    self._auth.active_auth_server
                ]
                await self.deregister_client(
                    self._auth.active_auth_server,
                    auth_config.client_id,
                    auth_config.registration_token,
                )
                del self._auth.servers[self._auth.active_server].authorization_servers[self._auth.active_auth_server]

            if self._auth.active_server and not self._auth.servers[self._auth.active_server].authorization_servers:
                del self._auth.servers[self._auth.active_server]

        self._auth.active_server = None
        self._auth.active_auth_server = None
        self._save()

    def get_server(self, server: str) -> Server | None:
        return self._auth.servers.get(server)

    @property
    def servers(self) -> list[str]:
        return list(self._auth.servers.keys())

    @property
    def active_server(self) -> str | None:
        return self._auth.active_server

    @active_server.setter
    def active_server(self, server: str | None) -> None:
        if server is not None and server not in self._auth.servers:
            raise ValueError(f"Server {server} not found")
        self._auth.active_server = server
        self._save()

    @property
    def active_auth_server(self) -> str | None:
        return self._auth.active_auth_server

    @active_auth_server.setter
    def active_auth_server(self, auth_server: str | None) -> None:
        if auth_server is not None and (
            self._auth.active_server not in self._auth.servers
            # pyrefly: ignore [bad-index]
            or auth_server not in self._auth.servers[self._auth.active_server].authorization_servers
        ):
            raise ValueError(f"Auth server {auth_server} not found in active server")
        self._auth.active_auth_server = auth_server
        self._save()
