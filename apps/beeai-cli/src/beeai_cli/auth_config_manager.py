# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import typing
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
    servers: dict[str, Server] = Field(default_factory=dict)
    active_server: str | None = None
    active_token: str | None = None


@typing.final
class AuthConfigManager:
    def __init__(self, config_path: pathlib.Path):
        self.config_path = config_path
        self.config: AuthConfig = self._load()

    def _load(self) -> AuthConfig:
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                return AuthConfig.parse_obj(data)
        return AuthConfig()

    def _save(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config.dict(), f, indent=2)

    def set_active_server(self, server: str) -> None:
        if server not in self.config.servers:
            raise ValueError(f"server {server} not found")
        self.config.active_server = server
        self._save()

    def get_active_server(self) -> str:
        return self.config.active_server or "http://localhost:8333"

    def set_active_token(self, server: str, auth_server: str) -> None:
        if server not in self.config.servers:
            raise ValueError(f"server {server} not found")
        if auth_server not in self.config.servers[server].authorization_servers:
            raise ValueError(f"Auth Server {auth_server} not found in server {server}")
        self.config.active_token = auth_server
        self._save()

    def save_auth_token(self, server: str, auth_server: str, token: dict[str, Any]) -> None:
        if server not in self.config.servers:
            self.config.servers[server] = Server()

        auth_token = AuthToken(**token)
        self.config.servers[server].authorization_servers[auth_server] = AuthServer(token=auth_token)
        self.config.active_token = auth_server
        self.config.active_server = server
        self._save()

    def load_auth_token(self) -> str | None:
        active_res = self.config.active_server
        active_token = self.config.active_token
        if not active_res or not active_token:
            return None
        server = self.config.servers.get(active_res)
        if not server:
            return None

        auth_server = server.authorization_servers.get(active_token)
        if not auth_server or not auth_server.token:
            return None

        return auth_server.token.access_token

    def clear_auth_token(self) -> None:
        active_res = self.config.active_server
        active_token = self.config.active_token
        if not active_res or not active_token:
            return None
        server = self.config.servers.get(active_res)
        if not server:
            return None
        if active_token in server.authorization_servers:
            del server.authorization_servers[active_token]

        if not server.authorization_servers:
            del self.config.servers[active_res]

        self.config.active_server = None
        self.config.active_token = None
        self._save()
