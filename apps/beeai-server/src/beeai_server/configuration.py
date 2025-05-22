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

import base64
import logging
from collections import defaultdict
from datetime import timedelta
from functools import cache
from pathlib import Path

from beeai_server.domain.registry import GithubRegistryLocation, RegistryLocation
from beeai_server.utils.github import GithubUrl
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfiguration(BaseModel):
    level: int = logging.INFO
    level_managed_provider: int = logging.INFO
    level_uvicorn: int = Field(default=logging.FATAL, validate_default=True)

    @model_validator(mode="after")
    def level_uvicorn_validator(self):
        if self.level == logging.DEBUG:
            self.level_uvicorn = logging.WARNING
        return self

    @field_validator("level", "level_uvicorn", "level_managed_provider", mode="before")
    def validate_level(cls, v: str | int | None):
        return v if isinstance(v, int) else logging.getLevelNamesMapping()[v]


class OCIRegistryConfiguration(BaseModel, extra="allow"):
    username: str | None = None
    password: str | None = None
    insecure: bool = False

    @property
    def protocol(self):
        return "http" if self.insecure else "https"

    @property
    def basic_auth_str(self) -> str | None:
        if self.username and self.password:
            return base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return None


class AgentRegistryConfiguration(BaseModel):
    enabled: bool = True
    location: RegistryLocation = GithubRegistryLocation(
        root=GithubUrl(root="https://github.com/i-am-bee/beeai-platform@release-v0.1.4#path=agent-registry.yaml")
    )
    preinstall: bool = False
    sync_period_sec: int = Field(default=timedelta(minutes=10).total_seconds())


class UIFeatureFlags(BaseModel):
    user_navigation: bool = Field(default=True)


class FeatureFlagsConfiguration(BaseModel):
    ui: UIFeatureFlags = UIFeatureFlags()


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__", extra="ignore"
    )

    logging: LoggingConfiguration = LoggingConfiguration()
    agent_registry: AgentRegistryConfiguration = AgentRegistryConfiguration()
    oci_registry: dict[str, OCIRegistryConfiguration] = Field(default_factory=dict)
    feature_flags: FeatureFlagsConfiguration = FeatureFlagsConfiguration()

    provider_config_path: Path = Path.home() / ".beeai" / "providers.yaml"
    telemetry_config_dir: Path = Path.home() / ".beeai" / "telemetry"
    env_path: Path = Path.home() / ".beeai" / ".env"
    cache_dir: Path = Path.home() / ".beeai" / "cache"

    port: int = 8333
    collector_host: AnyHttpUrl | None = "http://localhost:8335/"
    collector_managed: bool = True

    disable_docker: bool = False
    docker_host: str | None = None
    force_lima: bool = False
    autostart_providers: bool = False

    @model_validator(mode="after")
    def _oci_registry_defaultdict(self):
        oci_registry = defaultdict(OCIRegistryConfiguration)
        oci_registry.update(self.oci_registry)
        self.oci_registry = oci_registry
        return self


@cache
def get_configuration() -> Configuration:
    """Get cached configuration"""
    try:
        return Configuration()
    except ValidationError as ex:
        from beeai_server.logging_config import configure_logging

        configure_logging(configuration=LoggingConfiguration(level=logging.ERROR))

        logging.error(f"Improperly configured, Error: {ex!r}")
        raise ValueError("Improperly configured, make sure to supply all required variables") from ex
