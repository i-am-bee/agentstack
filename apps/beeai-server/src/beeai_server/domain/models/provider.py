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
import hashlib
import logging
from datetime import timedelta
from enum import StrEnum

from functools import cached_property
from uuid import UUID

import yaml

from acp_sdk import Agent as AcpAgent
from beeai_server.domain.constants import DOCKER_MANIFEST_LABEL_NAME
from beeai_server.domain.models.agent import EnvVar, Agent
from beeai_server.domain.models.registry import RegistryLocation
from beeai_server.exceptions import MissingConfigurationError
from beeai_server.utils.docker import DockerImageID, get_registry_image_config_and_labels
from httpx import AsyncClient
from kink import inject
from pydantic import BaseModel, Field, computed_field, RootModel, HttpUrl, model_validator

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

    @inject
    async def load_agents(self) -> list[AcpAgent]:
        from acp_sdk import AgentsListResponse

        _, labels = await get_registry_image_config_and_labels(self.root)
        if DOCKER_MANIFEST_LABEL_NAME not in labels:
            raise ValueError(f"Docker image labels must contain 'beeai.dev.agent.yaml': {self.location}")
        return AgentsListResponse.model_validate(
            yaml.safe_load(base64.b64decode(labels[DOCKER_MANIFEST_LABEL_NAME]))
        ).agents


class NetworkProviderLocation(RootModel):
    root: HttpUrl

    @property
    def provider_id(self) -> UUID:
        location_digest = hashlib.sha256(str(self.root).encode()).digest()
        return UUID(bytes=location_digest[:16])

    async def load_agents(self, provider_id: UUID) -> list[Agent]:
        from acp_sdk import AgentsListResponse

        async with AsyncClient() as client:
            response = await client.get(f"{str(self.root).rstrip('/')}/agents", timeout=1)
            return AgentsListResponse.model_validate(response.json()).agents


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


# class ManagedProvider(BaseProvider, extra="allow"):
#     @property
#     def _global_env(self) -> dict[str, str]:
#         return {
#             "OTEL_EXPORTER_OTLP_ENDPOINT": replace_localhost_url(OTEL_HTTP_ENDPOINT),
#             "PLATFORM_URL": "http://host.docker.internal:8333",
#         }
#
#     async def stop(self):
#         await self._container_exit_stack.aclose()
#
#     @inject
#     async def start(
#         self,
#         *,
#         configuration: Configuration,
#         container_backend: IContainerBackend,
#         env: dict[str, str] | None = None,
#         with_dummy_env: bool = True,
#         logs_container: LogsContainer | None = None,
#     ) -> str:
#         if not with_dummy_env:
#             self.check_env(env)
#
#         required_env_vars = {var.name for var in self.env if var.required}
#         env = {
#             **self._global_env,
#             **({var: "dummy" for var in required_env_vars} if with_dummy_env else {}),
#             **(self.extract_env(env=env)),
#         }
#         port = str(await find_free_port())


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
