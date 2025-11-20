# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import pathlib
import time
import typing
from collections import defaultdict
from typing import Any

import httpx
from pydantic import BaseModel, Field


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

    def _load(self) -> Auth:
        if not self._auth_path.exists():
            return Auth()
        return Auth.model_validate_json(self._auth_path.read_bytes())

    def _save(self) -> None:
        self._auth_path.write_text(self._auth.model_dump_json(indent=2))

    def save_auth_token(
        self,
        server: str,
        auth_server: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token: dict[str, Any] | None = None,
        registration_token: str | None = None,
    ) -> None:
        if auth_server is not None and client_id is not None and token is not None:
            if token["access_token"]:
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
        This method exchanges a refresh token for a new access token.
        """
        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            resp = None
            try:
                resp = await client.get(f"{auth_server}/.well-known/openid-configuration")
                resp.raise_for_status()
                oidc = resp.json()
            except Exception as e:
                if resp:
                    error_details = resp.json()
                    print(f"error: {error_details['error']} error description: {error_details['error_description']}")
                raise RuntimeError(f"OIDC discovery failed: {e}") from e

            token_endpoint = oidc["token_endpoint"]
            try:
                client_id = (
                    self._auth.servers[self._auth.active_server or ""].authorization_servers[auth_server].client_id
                )
                client_secret = (
                    self._auth.servers[self._auth.active_server or ""].authorization_servers[auth_server].client_secret
                )
                resp = await client.post(
                    f"{token_endpoint}",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": token.refresh_token,
                        "scope": token.scope,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                )
                resp.raise_for_status()
                new_token = resp.json()
            except Exception as e:
                if resp:
                    error_details = resp.json()
                    print(f"error: {error_details['error']} error description: {error_details['error_description']}")
                raise RuntimeError(f"Failed to refresh token: {e}") from e
            self.save_auth_token(
                self._auth.active_server or "",
                self._auth.active_auth_server or "",
                self._auth.servers[self._auth.active_server or ""].authorization_servers[auth_server].client_id or "",
                self._auth.servers[self._auth.active_server or ""].authorization_servers[auth_server].client_secret
                or "",
                token=new_token,
            )
            return new_token

    async def load_auth_token(self) -> str | None:
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

        if (auth_server.token.expires_at or 0) - 60 < time.time():
            new_token = await self.exchange_refresh_token(active_auth_server, auth_server.token)
            if new_token:
                return new_token["access_token"]
            return None

        return auth_server.token.access_token

    async def deregister_client(self, auth_server, client_id, registration_token) -> None:
        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            resp = None
            try:
                resp = await client.get(f"{auth_server}/.well-known/openid-configuration")
                resp.raise_for_status()
                oidc = resp.json()
                registration_endpoint = oidc["registration_endpoint"]
            except Exception as e:
                if resp:
                    error_details = resp.json()
                    print(f"error: {error_details['error']} error description: {error_details['error_description']}")
                raise RuntimeError(f"OIDC discovery failed: {e}") from e

            try:
                if client_id is not None and client_id != "" and registration_token is not None:
                    headers = {"authorization": f"bearer {registration_token}"}
                    resp = await client.delete(f"{registration_endpoint}/{client_id}", headers=headers)
                    resp.raise_for_status()

            except Exception as e:
                if resp:
                    error_details = resp.json()
                    print(f"error: {error_details['error']} error description: {error_details['error_description']}")
                raise RuntimeError(f"Dynamic client de-registration failed. {e}") from e

    async def clear_auth_token(self, all: bool = False) -> None:
        if all:
            for server in self._auth.servers:
                for auth_server in self._auth.servers[server].authorization_servers:
                    await self.deregister_client(
                        auth_server,
                        self._auth.servers[server].authorization_servers[auth_server].client_id,
                        self._auth.servers[server].authorization_servers[auth_server].registration_token,
                    )

            self._auth.servers = defaultdict(Server)
        else:
            if self._auth.active_server and self._auth.active_auth_server:
                if (
                    self._auth.servers[self._auth.active_server]
                    .authorization_servers[self._auth.active_auth_server]
                    .client_id
                ):
                    await self.deregister_client(
                        self._auth.active_auth_server,
                        self._auth.servers[self._auth.active_server]
                        .authorization_servers[self._auth.active_auth_server]
                        .client_id,
                        self._auth.servers[self._auth.active_server]
                        .authorization_servers[self._auth.active_auth_server]
                        .registration_token,
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
            or auth_server not in self._auth.servers[self._auth.active_server].authorization_servers
        ):
            raise ValueError(f"Auth server {auth_server} not found in active server")
        self._auth.active_auth_server = auth_server
        self._save()
