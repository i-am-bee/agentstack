# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import functools
import pathlib
from importlib.metadata import version

import pydantic
import pydantic_settings
from pydantic import SecretStr


@functools.cache
class Configuration(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=None, env_prefix="BEEAI__", env_nested_delimiter="__", extra="allow"
    )
    host: pydantic.AnyUrl = "http://localhost:8333"
    playground: str = "playground"
    debug: bool = False
    home: pathlib.Path = pathlib.Path.home() / ".beeai"
    agent_registry: pydantic.AnyUrl = (
        f"https://github.com/i-am-bee/beeai-platform@v{version('beeai-cli')}#path=agent-registry.yaml"
    )
    admin_password: SecretStr | None = None

    @property
    def lima_home(self) -> pathlib.Path:
        return self.home / "lima"

    @property
    def docker_home(self) -> pathlib.Path:
        return self.home / "docker"
