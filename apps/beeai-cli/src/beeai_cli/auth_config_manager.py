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
    config_version: typing.Literal[1] = 1
    servers: defaultdict[str, typing.Annotated[Server, Field(default_factory=Server)]] = Field(
        default_factory=lambda: defaultdict(Server)
    )
    active_server: str | None = None
    active_auth_server: str | None = None


@typing.final
class AuthConfigManager:
    def __init__(self, config_path: pathlib.Path):
        self._config_path = config_path
        self._config: AuthConfig = self._load()

    def _load(self) -> AuthConfig:
        if not self._config_path.exists():
            return AuthConfig()
        return AuthConfig.model_validate_json(self._config_path.read_bytes())

    def _save(self) -> None:
        self._config_path.write_text(self._config.model_dump_json(indent=2))

    def save_auth_token(self, server: str, auth_server: str | None = None, token: dict[str, Any] | None = None) -> None:
        if auth_server is not None and token is not None:
            self._config.servers[server].authorization_servers[auth_server] = AuthServer(token=AuthToken(**token))
        else:
            self._config.servers[server]  # touch
        self._config.active_server = server
        self._config.active_auth_server = auth_server
        self._save()

    def load_auth_token(self) -> str | None:
        active_res = self._config.active_server
        active_auth_server = self._config.active_auth_server
        if not active_res or not active_auth_server:
            return None
        server = self._config.servers.get(active_res)
        if not server:
            return None

        auth_server = server.authorization_servers.get(active_auth_server)
        if not auth_server or not auth_server.token:
            return None

        return auth_server.token.access_token

    def clear_auth_token(self, all: bool = False) -> None:
        if all:
            self._config.servers = defaultdict(Server)
        else:
            if self._config.active_server and self._config.active_auth_server:
                del self._config.servers[self._config.active_server].authorization_servers[
                    self._config.active_auth_server
                ]
            if (
                self._config.active_server
                and not self._config.servers[self._config.active_server].authorization_servers
            ):
                del self._config.servers[self._config.active_server]
        self._config.active_server = None
        self._config.active_auth_server = None
        self._save()

    def get_server(self, server: str) -> Server | None:
        return self._config.servers.get(server)

    @property
    def servers(self) -> list[str]:
        return list(self._config.servers.keys())

    @property
    def active_server(self) -> str | None:
        return self._config.active_server

    @active_server.setter
    def active_server(self, server: str | None) -> None:
        if server is not None and server not in self._config.servers:
            raise ValueError(f"Server {server} not found")
        self._config.active_server = server
        self._save()

    @property
    def active_auth_server(self) -> str | None:
        return self._config.active_auth_server

    @active_auth_server.setter
    def active_auth_server(self, auth_server: str | None) -> None:
        if auth_server is not None and (
            self._config.active_server not in self._config.servers
            or auth_server not in self._config.servers[self._config.active_server].authorization_servers
        ):
            raise ValueError(f"Auth server {auth_server} not found in active server")
        self._config.active_auth_server = auth_server
        self._save()
