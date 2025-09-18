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
    token: AuthToken | None = None


class Server(BaseModel):
    authorization_servers: dict[str, AuthServer] = Field(default_factory=dict)


class AuthConfig(BaseModel):
    servers: defaultdict[str, typing.Annotated[Server, Field(default_factory=Server)]] = Field(
        default_factory=lambda: defaultdict(Server)
    )
    active_server: str | None = None
    active_auth_server: str | None = None


@typing.final
class AuthConfigManager:
    def __init__(self, config_path: pathlib.Path):
        self.config_path = config_path
        self.config: AuthConfig = self._load()

    def _load(self) -> AuthConfig:
        if not self.config_path.exists():
            return AuthConfig()
        return AuthConfig.model_validate_json(self.config_path.read_bytes())

    def _save(self) -> None:
        self.config_path.write_text(self.config.model_dump_json(indent=2))

    def save_auth_token(self, server: str, auth_server: str, token: dict[str, Any]) -> None:
        self.config.servers[server].authorization_servers[auth_server] = AuthServer(token=AuthToken(**token))
        self.config.active_server = server
        self.config.active_auth_server = auth_server
        self._save()

    def load_auth_token(self) -> str | None:
        active_res = self.config.active_server
        active_auth_server = self.config.active_auth_server
        if not active_res or not active_auth_server:
            return None
        server = self.config.servers.get(active_res)
        if not server:
            return None

        auth_server = server.authorization_servers.get(active_auth_server)
        if not auth_server or not auth_server.token:
            return None

        return auth_server.token.access_token

    def clear_auth_token(self) -> None:
        active_res = self.config.active_server
        active_auth_server = self.config.active_auth_server
        if not active_res or not active_auth_server:
            return None
        server = self.config.servers.get(active_res)
        if not server:
            return None
        if active_auth_server in server.authorization_servers:
            del server.authorization_servers[active_auth_server]

        if not server.authorization_servers:
            del self.config.servers[active_res]

        self.config.active_server = None
        self.config.active_auth_server = None
        self._save()

    @property
    def servers(self) -> list[str]:
        return list(self.config.servers.keys())

    @property
    def active_server(self) -> str | None:
        return self.config.active_server

    @active_server.setter
    def active_server(self, server: str | None) -> None:
        if server is not None and server not in self.config.servers:
            raise ValueError(f"Server {server} not found")
        self.config.active_server = server
        self._save()

    @property
    def active_auth_server(self) -> str | None:
        return self.config.active_auth_server

    @active_auth_server.setter
    def active_auth_server(self, auth_server: str) -> None:
        if (
            not self.config.active_auth_server
            or self.config.active_server not in self.config.servers
            or auth_server not in self.config.servers[self.config.active_server].authorization_servers
        ):
            raise ValueError(f"Auth server {auth_server} not found in active server")
        self.config.active_auth_server = auth_server
        self._save()
