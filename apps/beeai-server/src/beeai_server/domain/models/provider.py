# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import logging
import re
from datetime import timedelta
from enum import StrEnum

from functools import cached_property
from typing import Any
from uuid import UUID

import yaml

from acp_sdk import AgentManifest as AcpAgent

from beeai_server.configuration import Configuration
from beeai_server.domain.constants import DOCKER_MANIFEST_LABEL_NAME
from beeai_server.domain.models.agent import EnvVar, Agent
from beeai_server.domain.models.registry import RegistryLocation
from beeai_server.exceptions import MissingConfigurationError
from beeai_server.utils.docker import DockerImageID, get_registry_image_config_and_labels
from httpx import AsyncClient
from kink import inject, di
from pydantic import BaseModel, Field, computed_field, RootModel, HttpUrl, model_validator, ModelWrapValidatorHandler

logger = logging.getLogger(__name__)


def convert_agents_from_acp(agents: list[AcpAgent], provider_id: UUID) -> list[Agent]:
    loaded_agents = []
    for agent in agents:
        metadata = agent.metadata.model_dump() | {"provider_id": provider_id}
        loaded_agents.append(Agent.model_validate(agent.model_dump() | {"metadata": metadata}))
    return loaded_agents


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
    async def load_agents(self) -> list[AcpAgent]:
        from acp_sdk import AgentsListResponse

        _, labels = await get_registry_image_config_and_labels(self.root)
        if DOCKER_MANIFEST_LABEL_NAME not in labels:
            raise ValueError(f"Docker image labels must contain 'beeai.dev.agent.yaml': {str(self.root)}")
        return AgentsListResponse.model_validate(
            yaml.safe_load(base64.b64decode(labels[DOCKER_MANIFEST_LABEL_NAME]))
        ).agents


class NetworkProviderLocation(RootModel):
    root: HttpUrl

    @model_validator(mode="wrap")
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

    async def load_agents(self, provider_id: UUID) -> list[Agent]:
        from acp_sdk import AgentsListResponse

        async with AsyncClient() as client:
            try:
                response = await client.get(f"{str(self.root).rstrip('/')}/agents", timeout=1)
                return AgentsListResponse.model_validate(response.json()).agents
            except Exception as ex:
                raise ValueError(f"Unable to load agents from location: {self.root}: {ex}") from ex


ProviderLocation = DockerImageProviderLocation | NetworkProviderLocation


class Provider(BaseModel):
    auto_stop_timeout: timedelta = Field(default=timedelta(minutes=5))
    source: ProviderLocation
    registry: RegistryLocation | None = None
    env: list[EnvVar]
    auto_remove: bool = False

    @model_validator(mode="after")
    def auto_remove_only_unmanaged(self):
        if self.auto_remove and self.managed:
            raise ValueError("auto_remove can only be set for unmanaged providers")
        return self

    @computed_field()
    @cached_property
    def managed(self) -> bool:
        return isinstance(self.source, DockerImageProviderLocation)

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
