# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import functools
import importlib.metadata
import pathlib
import re

import pydantic
import pydantic_settings
from pydantic import SecretStr


@functools.cache
def version():
    # Python strips '-', we need to re-insert it: 1.2.3rc1 -> 1.2.3-rc1
    return re.sub(r"([0-9])([a-z])", r"\1-\2", importlib.metadata.version("beeai-cli"))


@functools.cache
class Configuration(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_prefix="BEEAI__", env_nested_delimiter="__", extra="allow"
    )
    host: pydantic.AnyUrl = "http://localhost:8333"
    ui_url: pydantic.AnyUrl = "http://localhost:8334"
    playground: str = "playground"
    debug: bool = False
    home: pathlib.Path = pathlib.Path.home() / ".beeai"
    agent_registry: pydantic.AnyUrl = (
        f"https://github.com/i-am-bee/beeai-platform@v{version()}#path=agent-registry.yaml"
    )
    admin_password: SecretStr | None = None
    oidc_enabled: bool = False
    @property
    def lima_home(self) -> pathlib.Path:
        return self.home / "lima"
