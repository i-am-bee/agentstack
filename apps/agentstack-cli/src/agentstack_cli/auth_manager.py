# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pathlib
import typing
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, Field


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


class AuthServer(BaseModel):
    client_id: str = "df82a687-d647-4247-838b-7080d7d83f6c"  # Backwards compatibility default
    client_secret: str | None = None
    token: AuthToken | None = None


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
    ) -> None:
        if auth_server is not None and client_id is not None and token is not None:
            self._auth.servers[server].authorization_servers[auth_server] = AuthServer(
                client_id=client_id, client_secret=client_secret, token=AuthToken(**token)
            )
        else:
            self._auth.servers[server]  # touch
        self._save()

    def load_auth_token(self) -> str | None:
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

        return auth_server.token.access_token

    def clear_auth_token(self, all: bool = False) -> None:
        if all:
            self._auth.servers = defaultdict(Server)
        else:
            if self._auth.active_server and self._auth.active_auth_server:
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
