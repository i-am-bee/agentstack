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

from pydantic_core.core_schema import ValidationInfo

from beeai_server.domain.models.registry import RegistryLocation
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator, AnyUrl, Secret
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class LoggingConfiguration(BaseModel):
    level: int = logging.INFO
    level_uvicorn: int = Field(default=logging.FATAL, validate_default=True)
    level_sqlalchemy: int = Field(default=None, validate_default=True)

    @model_validator(mode="after")
    def level_uvicorn_validator(self):
        if self.level == logging.DEBUG:
            self.level_uvicorn = logging.WARNING
        return self

    @field_validator("level_sqlalchemy", mode="before")
    def level_sqlalchemy_validator(cls, v: str | int | None, info: ValidationInfo):
        if v is not None:
            return cls.validate_level(v)
        return logging.INFO if cls.validate_level(info.data["level"]) == logging.DEBUG else logging.WARNING

    @field_validator("level", "level_uvicorn", mode="before")
    def validate_level(cls, v: str | int | None):
        return v if isinstance(v, int) else logging.getLevelNamesMapping()[v.upper()]


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
    locations: dict[str, RegistryLocation] = Field(default_factory=dict)
    sync_period_sec: int = Field(default=timedelta(minutes=10).total_seconds())


class AuthConfiguration(BaseModel):
    admin_password: Secret[str] | None = Field(default=None)
    disable_auth: bool = False

    @model_validator(mode="after")
    def validate_auth(self):
        if self.disable_auth:
            logger.critical("Authentication is disabled! This is suitable only for local (desktop) deployment.")
            return self
        if self.admin_password is None:
            raise ValueError("Admin password must be provided if authentication is enabled")
        return self


class PersistenceConfiguration(BaseModel):
    db_url: Secret[AnyUrl] = Secret(AnyUrl("postgresql+asyncpg://beeai-user:password@postgresql:5432/beeai"))
    encryption_key: Secret[str] | None = None
    finished_requests_remove_after_sec: int = timedelta(minutes=30).total_seconds()
    stale_requests_remove_after_sec: int = timedelta(hours=1).total_seconds()


class TelemetryConfiguration(BaseModel):
    collector_url: AnyUrl = AnyUrl("http://otel-collector-svc:8335")


class UIFeatureFlags(BaseModel):
    user_navigation: bool = Field(default=True)


class FeatureFlagsConfiguration(BaseModel):
    ui: UIFeatureFlags = UIFeatureFlags()


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__", extra="ignore"
    )

    auth: AuthConfiguration = Field(default_factory=AuthConfiguration)
    logging: LoggingConfiguration = Field(default_factory=LoggingConfiguration)
    agent_registry: AgentRegistryConfiguration = Field(default_factory=AgentRegistryConfiguration)
    oci_registry: dict[str, OCIRegistryConfiguration] = Field(default_factory=dict)
    telemetry: TelemetryConfiguration = Field(default_factory=TelemetryConfiguration)
    persistence: PersistenceConfiguration = Field(default_factory=PersistenceConfiguration)
    k8s_namespace: str | None = None
    k8s_kubeconfig: Path | None = None

    self_registration_use_local_network: bool = Field(
        False,
        description="Which network to use for self-registered providers - should be False when running in cluster",
    )

    feature_flags: FeatureFlagsConfiguration = FeatureFlagsConfiguration()

    platform_service_url: str = "beeai-platform-svc:8333"
    port: int = 8333

    base_path: str = "/"

    @model_validator(mode="after")
    def _oci_registry_defaultdict(self):
        oci_registry = defaultdict(OCIRegistryConfiguration)
        oci_registry.update(self.oci_registry)
        self.oci_registry = oci_registry
        return self

    @model_validator(mode="after")
    def _base_path_ends_in_slash(self):
        if not self.base_path.endswith("/"):
            self.base_path += "/"
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
