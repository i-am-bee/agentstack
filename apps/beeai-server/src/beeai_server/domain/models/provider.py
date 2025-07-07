# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import json
import logging
import re
from datetime import timedelta
from enum import StrEnum
from functools import cached_property
from typing import Any
from uuid import UUID

from a2a.types import AgentCard
from httpx import AsyncClient
from kink import di, inject
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    HttpUrl,
    ModelWrapValidatorHandler,
    RootModel,
    computed_field,
    model_validator,
)

from beeai_server.configuration import Configuration
from beeai_server.domain.constants import DOCKER_MANIFEST_LABEL_NAME, REQUIRED_ENV_EXTENSION_URI
from beeai_server.domain.models.registry import RegistryLocation
from beeai_server.exceptions import MissingConfigurationError
from beeai_server.utils.docker import DockerImageID, get_registry_image_config_and_labels
from beeai_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


class DockerImageProviderLocation(RootModel):
    root: DockerImageID

    @property
    def provider_id(self) -> UUID:
        location_digest = hashlib.sha256(str(self.root).encode()).digest()
        return UUID(bytes=location_digest[:16])

    @property
    def is_on_host(self) -> bool:
        return False

    @inject
    async def load_agent_card(self) -> AgentCard:
        from a2a.types import AgentCard

        _, labels = await get_registry_image_config_and_labels(self.root)
        if DOCKER_MANIFEST_LABEL_NAME not in labels:
            raise ValueError(f"Docker image labels must contain 'beeai.dev.agent.json': {self.root!s}")
        return AgentCard.model_validate(json.loads(base64.b64decode(labels[DOCKER_MANIFEST_LABEL_NAME])))


class NetworkProviderLocation(RootModel):
    root: HttpUrl

    @model_validator(mode="wrap")
    @classmethod
    def _replace_localhost_url(cls, data: Any, handler: ModelWrapValidatorHandler):
        configuration = di[Configuration]
        url: NetworkProviderLocation = handler(data)
        if configuration.provider.self_registration_use_local_network:
            url.root = HttpUrl(re.sub(r"host.docker.internal", "localhost", str(url.root)))
        else:
            # localhost does not make sense in k8s environment, replace it with host.docker.internal for backward compatibility
            url.root = HttpUrl(re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", str(url.root)))
        return url

    @property
    def is_on_host(self) -> bool:
        """
        Return True for self-registered providers which need to be treated a bit differently
        """
        return any(url in str(self.root) for url in {"host.docker.internal", "localhost", "127.0.0.1"})

    @property
    def provider_id(self) -> UUID:
        location_digest = hashlib.sha256(str(self.root).encode()).digest()
        return UUID(bytes=location_digest[:16])

    async def load_agent_card(self) -> AgentCard:
        from a2a.types import AgentCard

        async with AsyncClient() as client:
            try:
                response = await client.get(f"{str(self.root).rstrip('/')}/.well-known/agent.json", timeout=1)
                response.raise_for_status()
                return AgentCard.model_validate(response.json())
            except Exception as ex:
                raise ValueError(f"Unable to load agents from location: {self.root}: {ex}") from ex


class EnvVar(BaseModel):
    name: str
    description: str | None = None
    required: bool = False


ProviderLocation = DockerImageProviderLocation | NetworkProviderLocation


class Provider(BaseModel):
    auto_stop_timeout: timedelta = Field(default=timedelta(minutes=5))
    source: ProviderLocation
    registry: RegistryLocation | None = None
    auto_remove: bool = False
    created_at: AwareDatetime = Field(default_factory=utc_now)
    last_active_at: AwareDatetime = Field(default_factory=utc_now)
    agent_card: AgentCard

    @model_validator(mode="after")
    def auto_remove_only_unmanaged(self):
        if self.auto_remove and self.managed:
            raise ValueError("auto_remove can only be set for unmanaged providers")
        return self

    @computed_field()
    @cached_property
    def managed(self) -> bool:
        return isinstance(self.source, DockerImageProviderLocation)

    @computed_field()
    @cached_property
    def env(self) -> list[EnvVar]:
        try:
            extensions = self.agent_card.capabilities.extensions or []
            env = next(ext for ext in extensions if ext.uri == REQUIRED_ENV_EXTENSION_URI).params["env"]
            return [EnvVar.model_validate(var) for var in env]
        except StopIteration:
            return []

    @computed_field
    @property
    def id(self) -> UUID:
        return self.source.provider_id

    def check_env(self, env: dict[str, str] | None = None, raise_error: bool = True) -> list[EnvVar]:
        env = env or {}
        required_env = {var.name for var in self.env if var.required}
        all_env = {var.name for var in self.env}
        missing_env = [var for var in self.env if var.name in all_env - env.keys()]
        missing_required_env = [var for var in self.env if var.name in required_env - env.keys()]
        if missing_required_env and raise_error:
            raise MissingConfigurationError(missing_env=missing_env)
        return missing_env

    def extract_env(self, env: dict[str, str] | None = None) -> dict[str, str]:
        env = env or {}
        declared_env_vars = {var.name for var in self.env}
        return {var: env[var] for var in env if var in declared_env_vars}


class ProviderDeploymentState(StrEnum):
    missing = "missing"
    starting = "starting"
    ready = "ready"
    running = "running"
    error = "error"


class ProviderErrorMessage(BaseModel):
    message: str


class ProviderWithState(Provider, extra="allow"):
    state: ProviderDeploymentState
    last_error: ProviderErrorMessage | None = None
    missing_configuration: list[EnvVar] = Field(default_factory=list)
