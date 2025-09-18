# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
from typing import Any

from pydantic import SecretStr


class AuthConfigManager:
    def __init__(self, config_path: pathlib.Path):
        self.config_path = config_path
        self.config: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        return {"servers": {}, "active_server": None, "active_token": None}

    def _save(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def set_active_server(self, server: str) -> None:
        if server not in self.config["servers"]:
            raise ValueError(f"server {server} not found")
        self.config["active_server"] = server
        self._save()

    def get_active_server(self) -> str:
        return self.config["active_server"]

    def set_active_token(self, server: str, auth_server: str) -> None:
        if server not in self.config["servers"]:
            raise ValueError(f"server {server} not found")
        if auth_server not in self.config["servers"][server]["authorization_servers"]:
            raise ValueError(f"Auth Server {auth_server} not found in server {server}")
        self.config["active_token"] = auth_server
        self._save()

    def save_auth_token(self, server: str, auth_server: str, token: dict[str, Any]) -> None:
        servers = self.config["servers"]
        if server not in servers:
            servers[server] = {"authorization_servers": {}}

        servers[server]["authorization_servers"][auth_server] = {"token": token}
        self.config["active_token"] = auth_server
        self.config["active_server"] = server
        self._save()

    def load_auth_token(self) -> SecretStr | None:
        active_res = self.config["active_server"]
        active_token = self.config["active_token"]
        if not active_res or not active_token:
            return None
        server = self.config["servers"].get(active_res)
        if not server:
            return None

        access_token = server["authorization_servers"].get(active_token, {}).get("token").get("access_token")
        return SecretStr(access_token) if access_token else None

    def clear_auth_token(self) -> None:
        active_res = self.config["active_server"]
        active_token = self.config["active_token"]
        if not active_res or not active_token:
            return None
        server = self.config["servers"].get(active_res)
        if not server:
            return None
        if active_token in server["authorization_servers"]:
            del server["authorization_servers"][active_token]

        if not server["authorization_servers"]:
            del self.config["servers"][active_res]

        self.config["active_server"] = None
        self.config["active_token"] = None
        self._save()
