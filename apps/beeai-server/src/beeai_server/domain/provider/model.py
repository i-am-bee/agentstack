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

import abc
import base64
import hashlib
import logging
from abc import abstractmethod
from contextlib import suppress, AsyncExitStack
from datetime import timedelta
from enum import StrEnum
from typing import Any, Optional, Self

from acp_sdk.models import Agent as AcpAgent, Metadata as AcpMetadata
from functools import cached_property

import yaml
from aiodocker import DockerError

from beeai_server.adapters.interface import IContainerBackend
from beeai_server.configuration import Configuration
from beeai_server.custom_types import ID
from beeai_server.domain.constants import DOCKER_MANIFEST_LABEL_NAME, LOCAL_IMAGE_REGISTRY
from beeai_server.domain.registry import RegistryLocation
from beeai_server.exceptions import MissingConfigurationError, retry_if_exception_grp_type
from beeai_server.telemetry import OTEL_HTTP_ENDPOINT
from beeai_server.utils.docker import DockerImageID, get_registry_image_config_and_labels, replace_localhost_url
from beeai_server.utils.github import ResolvedGithubUrl, GithubUrl
from beeai_server.utils.logs_container import LogsContainer
from beeai_server.utils.process import find_free_port
from httpx import HTTPError, AsyncClient
from kink import inject
from pydantic import AnyUrl, BaseModel, Field, PrivateAttr, computed_field, RootModel, AnyHttpUrl
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EnvVar(BaseModel):
    name: str
    description: str | None = None
    required: bool = False


class Metadata(AcpMetadata):
    env: list[EnvVar] = Field(default_factory=list, description="For configuration -- passed to the process")
    ui: dict[str, Any] | None = None
    provider: str | None = None


class Agent(AcpAgent, extra="allow"):
    metadata: Metadata = Metadata()


class ProviderManifest(BaseModel, extra="allow"):
    agents: list[Agent]


class BaseProviderSource(BaseModel, abc.ABC):
    location: Any

    @computed_field
    @property
    def id(self) -> ID:
        return hashlib.sha256(str(self.location).encode()).hexdigest()[:16]

    @abstractmethod
    async def load_manifest(self) -> ProviderManifest: ...
    async def install(self, logs_container: LogsContainer | None = None): ...
    async def uninstall(self): ...

    async def is_installed(self):
        return True

    def __str__(self):
        return str(self.location)


class GithubProviderSource(BaseProviderSource):
    location: ResolvedGithubUrl

    _resolved: bool = PrivateAttr(False)

    @property
    def image_id(self) -> DockerImageID:
        base_tag = f"{LOCAL_IMAGE_REGISTRY}/{self.location.org}/{self.location.repo}"
        if self.location.path:
            base_tag += f"/{self.location.path.replace('/', '_')}"
        return DockerImageID(root=f"{base_tag}:{self.location.version}")

    @inject
    async def install(self, container_backend: IContainerBackend, logs_container: LogsContainer | None = None):
        await container_backend.build_from_github(
            github_url=self.location, destination=self.image_id, logs_container=logs_container
        )

    @inject
    async def uninstall(self, container_backend: IContainerBackend):
        await container_backend.delete_image(image=self.image_id)

    @inject
    async def is_installed(self, container_backend: IContainerBackend) -> bool:
        return await container_backend.check_image(image=self.image_id)

    @inject
    async def load_manifest(self, container_backend: IContainerBackend) -> ProviderManifest:
        if not await self.is_installed():
            raise RuntimeError(
                "Github provider does not support static agent discovery, agents need to be installed first."
            )
        labels = await container_backend.extract_labels(image=self.image_id)
        if DOCKER_MANIFEST_LABEL_NAME not in labels:
            raise ValueError(f"Docker image labels must contain 'beeai.dev.agent.yaml': {self.location}")
        return ProviderManifest.model_validate(yaml.safe_load(base64.b64decode(labels[DOCKER_MANIFEST_LABEL_NAME])))


class DockerImageProviderSource(BaseProviderSource):
    location: DockerImageID

    @property
    def image_id(self) -> DockerImageID:
        return self.location

    @inject
    async def load_manifest(self, container_backend: IContainerBackend) -> ProviderManifest:
        if await self.is_installed():
            labels = await container_backend.extract_labels(image=self.image_id)
        else:
            _, labels = await get_registry_image_config_and_labels(self.location)
        if DOCKER_MANIFEST_LABEL_NAME not in labels:
            raise ValueError(f"Docker image labels must contain 'beeai.dev.agent.yaml': {self.location}")
        return ProviderManifest.model_validate(yaml.safe_load(base64.b64decode(labels[DOCKER_MANIFEST_LABEL_NAME])))

    @inject
    async def install(self, container_backend: IContainerBackend, logs_container: LogsContainer | None = None):
        await container_backend.pull_image(image=self.location, logs_container=logs_container)

    @inject
    async def uninstall(self, container_backend: IContainerBackend):
        await container_backend.delete_image(image=self.image_id)

    @inject
    async def is_installed(self, container_backend: IContainerBackend) -> bool:
        return await container_backend.check_image(image=self.image_id)


class NetworkProviderSource(BaseProviderSource):
    location: AnyHttpUrl

    @inject
    async def load_manifest(self, container_backend: IContainerBackend) -> ProviderManifest:
        async with AsyncClient() as client:
            response = await client.get(f"{str(self.location).rstrip('/')}/agents", timeout=1)
            return ProviderManifest.model_validate(response.json())


ManagedProviderSource = GithubProviderSource | DockerImageProviderSource
UnmanagedProviderSource = NetworkProviderSource


class BaseProvider(BaseModel, abc.ABC):
    manifest: ProviderManifest
    auto_stop_timeout: timedelta | None = Field(None, exclude=True)
    source: UnmanagedProviderSource | ManagedProviderSource
    registry: RegistryLocation | None = None
    persistent: bool = True

    @computed_field()
    @cached_property
    def id(self) -> ID:
        return self.source.id

    @computed_field()
    @cached_property
    def location(self) -> ID:
        return str(self.source)

    @classmethod
    async def load_from_source(
        cls,
        source: ManagedProviderSource | UnmanagedProviderSource,
        registry: RegistryLocation | None = None,
        persistent: bool = True,
    ) -> Self:
        manifest = await source.load_manifest()
        return cls(manifest=manifest, source=source, registry=registry, persistent=persistent)

    @cached_property
    def env(self):
        return [EnvVar.model_validate(env) for agent in self.manifest.agents for env in agent.metadata.env]

    def check_env(self, env: dict[str, str] | None = None, raise_error: bool = True) -> list[EnvVar]:
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

    async def is_installed(self) -> bool:
        return True

    async def install(self, logs_container: LogsContainer | None = None):
        pass

    async def uninstall(self):
        pass

    @abc.abstractmethod
    async def start(
        self,
        *,
        env: dict[str, str] | None = None,
        with_dummy_env: bool = True,
        logs_container: Optional["LogsContainer"] = None,
    ) -> str:
        """
        :param env: environment values passed to the process
        :param with_dummy_env: substitute all unfilled required variables from manifest by "dummy" value
        :param logs_container: capture logs of the provider process (if managed)
        """

    async def stop(self):
        pass

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.stop()


class ManagedProvider(BaseProvider, extra="allow"):
    source: ManagedProviderSource
    auto_stop_timeout: timedelta | None = Field(timedelta(minutes=5), exclude=True)
    _container_exit_stack: AsyncExitStack = PrivateAttr(default_factory=AsyncExitStack)

    @computed_field
    @property
    def image_id(self) -> DockerImageID:
        return self.source.image_id

    async def is_installed(self) -> bool:
        return await self.source.is_installed()

    async def install(self, logs_container: LogsContainer | None = None):
        if await self.source.is_installed():
            return
        await self.source.install(logs_container=logs_container)

    async def uninstall(self):
        with suppress(DockerError):
            await self.source.uninstall()

    @property
    def _global_env(self) -> dict[str, str]:
        return {
            "PORT": "8000",
            "HOST": "0.0.0.0",
            "OTEL_EXPORTER_OTLP_ENDPOINT": replace_localhost_url(OTEL_HTTP_ENDPOINT),
            "PLATFORM_URL": "http://host.docker.internal:8333",
            "LLM_MODEL": "dummy",
            "LLM_API_KEY": "dummy",
            "LLM_API_BASE": "http://host.docker.internal:8333/api/v1/llm",
        }

    async def stop(self):
        await self._container_exit_stack.aclose()

    @inject
    async def start(
        self,
        *,
        configuration: Configuration,
        container_backend: IContainerBackend,
        env: dict[str, str] | None = None,
        with_dummy_env: bool = True,
        logs_container: LogsContainer | None = None,
    ) -> str:
        if not with_dummy_env:
            self.check_env(env)

        env = {
            **({var.name: "dummy" for var in self.env if var.required} if with_dummy_env else {}),
            **(self.extract_env(env=env)),
            **self._global_env,
        }
        port = str(await find_free_port())

        try:
            await self._container_exit_stack.enter_async_context(
                container_backend.open_container(
                    image=self.image_id,
                    port_mappings={port: "8000"},
                    env=env,
                    logs_container=logs_container,
                )
            )
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(8),
                wait=wait_exponential(multiplier=1, max=3),
                retry=retry_if_exception_grp_type(HTTPError),
                reraise=True,
            ):
                with attempt:
                    async with AsyncClient() as client:
                        base_url = f"http://localhost:{port}/"
                        await client.get(f"{base_url}agents", timeout=1)
            return base_url
        except BaseException:
            await self._container_exit_stack.aclose()
            raise


class UnmanagedProvider(BaseProvider, extra="allow"):
    source: UnmanagedProviderSource

    async def start(self, *_args, **_kwargs) -> str:
        base_url = f"{str(self.source.location).rstrip('/')}/"
        async with AsyncClient(base_url=base_url) as client:
            await client.get("agents")
        return base_url


Provider = ManagedProvider | UnmanagedProvider


class GithubProviderLocation(RootModel):
    root: GithubUrl

    async def get_source(self) -> GithubProviderSource:
        return GithubProviderSource(location=await self.root.resolve_version())

    @inject
    async def load(
        self, configuration: Configuration, *, registry: RegistryLocation | None = None, persistent: bool = True
    ) -> ManagedProvider:
        if configuration.disable_docker:
            raise RuntimeError("Cannot load managed provider when docker is disabled in the configuration.")
        return await ManagedProvider.load_from_source(
            source=await self.get_source(), registry=registry, persistent=persistent
        )


class DockerImageProviderLocation(RootModel):
    root: DockerImageID

    async def get_source(self) -> DockerImageProviderSource:
        return DockerImageProviderSource(location=self.root)

    @inject
    async def load(
        self, configuration: Configuration, *, registry: RegistryLocation | None = None, persistent: bool = True
    ) -> ManagedProvider:
        if configuration.disable_docker:
            raise RuntimeError("Cannot load managed provider when docker is disabled in the configuration.")
        return await ManagedProvider.load_from_source(await self.get_source(), registry=registry, persistent=persistent)


class NetworkProviderLocation(RootModel):
    root: AnyUrl

    async def get_source(self) -> NetworkProviderSource:
        return NetworkProviderSource(location=self.root)

    async def load(self, *, registry: RegistryLocation | None = None, persistent: bool = True) -> UnmanagedProvider:
        return await UnmanagedProvider.load_from_source(
            await self.get_source(), registry=registry, persistent=persistent
        )


ProviderLocation = GithubProviderLocation | DockerImageProviderLocation | NetworkProviderLocation


class ProviderStatus(StrEnum):
    not_loaded = "not_loaded"
    not_installed = "not_installed"
    install_error = "install_error"
    installing = "installing"
    starting = "starting"
    ready = "ready"
    running = "running"
    error = "error"


class ProviderErrorMessage(BaseModel):
    message: str
