# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import pathlib

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
        "https://github.com/i-am-bee/beeai-platform@release-v0.2.0#path=agent-registry.yaml"
    )
    admin_password: SecretStr | None = None

    @property
    def lima_home(self) -> pathlib.Path:
        return self.home / "lima"

    @property
    def docker_home(self) -> pathlib.Path:
        return self.home / "docker"
