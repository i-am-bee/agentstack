# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
from typing import Any

from pydantic import SecretStr

from beeai_cli.utils import make_safe_name


class AuthConfigManager:
    def __init__(self, config_path: pathlib.Path):
        self.config_path = config_path
        self.config: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        return {"resources": {}, "active_resource": None, "active_token": None}

    def _save(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def set_active_resource(self, resource: str) -> None:
        resource = make_safe_name(resource)
        if resource not in self.config["resources"]:
            raise ValueError(f"Resource {resource} not found")
        self.config["active_resource"] = resource
        self._save()

    def set_active_token(self, resource: str, auth_server: str) -> None:
        resource = make_safe_name(resource)
        if resource not in self.config["resources"]:
            raise ValueError(f"Resource {resource} not found")
        if auth_server not in self.config["resources"][resource]["authorization_servers"]:
            raise ValueError(f"Auth Server {auth_server} not found in resource {resource}")
        self.config["active_token"] = auth_server
        self._save()

    def save_auth_token(self, resource: str, auth_server: str, token: dict[str, Any]) -> None:
        resource = make_safe_name(resource)
        resources = self.config["resources"]
        if resource not in resources:
            resources[resource] = {"authorization_servers": {}}

        resources[resource]["authorization_servers"][auth_server] = {"token": token}
        self.config["active_token"] = auth_server
        self.config["active_resource"] = resource
        self._save()

    def load_auth_token(self) -> SecretStr | None:
        active_res = self.config["active_resource"]
        active_token = self.config["active_token"]
        if not active_res or not active_token:
            return None
        resource = self.config["resources"].get(active_res)
        if not resource:
            return None

        access_token = resource["authorization_servers"].get(active_token, {}).get("token").get("access_token")
        return SecretStr(access_token) if access_token else None

    def clear_auth_token(self) -> None:
        active_res = self.config["active_resource"]
        active_token = self.config["active_token"]
        if not active_res or not active_token:
            return None
        resource = self.config["resources"].get(active_res)
        if not resource:
            return None
        if active_token in resource["authorization_servers"]:
            del resource["authorization_servers"][active_token]

        if not resource["authorization_servers"]:
            del self.config["resources"][active_res]

        self.config["active_resource"] = None
        self.config["active_token"] = None
        self._save()
