# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import json
import logging
from datetime import timedelta
from enum import StrEnum
from typing import Any
from urllib.parse import quote, urljoin
from uuid import UUID

from a2a.types import AgentCard
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
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

from agentstack_server.configuration import Configuration
from agentstack_server.domain.constants import (
    AGENT_DETAIL_EXTENSION_URI,
    DEFAULT_AUTO_STOP_TIMEOUT,
    DOCKER_MANIFEST_LABEL_NAME,
    SELF_REGISTRATION_EXTENSION_URI,
)
from agentstack_server.domain.models.registry import RegistryLocation
from agentstack_server.domain.utils import bridge_k8s_to_localhost, bridge_localhost_to_k8s
from agentstack_server.exceptions import MissingConfigurationError, VersionResolveError
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.docker import DockerImageID, ResolvedDockerImageID
from agentstack_server.utils.github import ResolvedGithubUrl
from agentstack_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


class VersionInfo(BaseModel):
    docker: ResolvedDockerImageID | None = None
    github: ResolvedGithubUrl | None = None


class DockerImageProviderLocation(RootModel):
    root: DockerImageID

    _resolved_version: ResolvedDockerImageID | None = None

    @property
    def provider_id(self) -> UUID:
        location_digest = hashlib.sha256(str(self.root).encode()).digest()
        return UUID(bytes=location_digest[:16])

    @property
    def is_on_host(self) -> bool:
        return False

    @property
    def origin(self) -> str:
        return self.root.base

    async def get_resolved_version(self) -> ResolvedDockerImageID:
        if not self._resolved_version:
            try:
                self._resolved_version = await self.root.resolve_version()
            except Exception as ex:
                raise VersionResolveError(str(self.root), str(ex)) from ex
        return self._resolved_version

    async def get_version_info(self) -> VersionInfo:
        return VersionInfo(docker=await self.get_resolved_version())

    @inject
    async def load_agent_card(self) -> AgentCard:
        from a2a.types import AgentCard

        resolved_version = await self.get_resolved_version()
        labels = await resolved_version.get_labels()
        if DOCKER_MANIFEST_LABEL_NAME not in labels:
            raise ValueError(f"Docker image labels must contain 'agentstack.dev.agent.json': {self.root!s}")
        return AgentCard.model_validate(json.loads(base64.b64decode(labels[DOCKER_MANIFEST_LABEL_NAME])))


class NetworkProviderLocation(RootModel):
    root: HttpUrl

    @property
    def origin(self) -> str:
        return str(self.root)

    @property
    def a2a_url(self):
        """Clean url with no query or fragment parts"""
        assert self.root.host, "Host is required"
        return HttpUrl.build(
            scheme=self.root.scheme,
            host=self.root.host,
            port=self.root.port,
            path=self.root.path.lstrip("/") if self.root.path else None,
        )

    async def get_version_info(self) -> VersionInfo:
        return VersionInfo()

    @model_validator(mode="wrap")
    @classmethod
    def _replace_localhost_url(cls, data: Any, handler: ModelWrapValidatorHandler):
        configuration = di[Configuration]
        url: NetworkProviderLocation = handler(data)
        if configuration.provider.self_registration_use_local_network:
            url.root = bridge_k8s_to_localhost(url.root)
        else:
            # localhost does not make sense in k8s environment, replace it with host.docker.internal for backward compatibility
            url.root = bridge_localhost_to_k8s(url.root)
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
                response = await client.get(urljoin(str(self.a2a_url), AGENT_CARD_WELL_KNOWN_PATH), timeout=1)
                response.raise_for_status()
                card = AgentCard.model_validate(response.json())
                if ext := get_extension(card, SELF_REGISTRATION_EXTENSION_URI):
                    assert ext.params
                    self_registration_id = ext.params["self_registration_id"]
                    if quote(self.root.fragment or "", safe="") != quote(self_registration_id, safe=""):
                        raise ValueError(
                            f"Self registration id does not match: {self.root.fragment} != {self_registration_id}"
                        )
                return card
            except Exception as ex:
                raise ValueError(f"Unable to load agents from location: {self.root}: {ex}") from ex


class EnvVar(BaseModel, extra="allow"):
    name: str
    description: str | None = None
    required: bool = False


class UnmanagedState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class ProviderType(StrEnum):
    MANAGED = "managed"
    UNMANAGED = "unmanaged"


ProviderLocation = DockerImageProviderLocation | NetworkProviderLocation


class Provider(BaseModel):
    source: ProviderLocation
    id: UUID = Field(default_factory=lambda data: data["source"].provider_id)
    auto_stop_timeout: timedelta = Field(default=DEFAULT_AUTO_STOP_TIMEOUT)
    origin: str  # docker or github respository
    version_info: VersionInfo = Field(default_factory=VersionInfo)
    registry: RegistryLocation | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    last_active_at: AwareDatetime = Field(default_factory=utc_now)
    agent_card: AgentCard
    unmanaged_state: UnmanagedState | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def type(self) -> ProviderType:
        return ProviderType.MANAGED if isinstance(self.source, DockerImageProviderLocation) else ProviderType.UNMANAGED

    @model_validator(mode="after")
    def unmanaged_fields_discrimination(self):
        if self.unmanaged_state and self.type == ProviderType.MANAGED:
            raise ValueError("unmanaged_state can only be set for unmanaged providers")
        return self

    @computed_field
    @property
    def managed(self) -> bool:
        return self.type == ProviderType.MANAGED

    @computed_field
    @property
    def env(self) -> list[EnvVar]:
        if agent_detail := get_extension(self.agent_card, AGENT_DETAIL_EXTENSION_URI):
            variables = agent_detail.model_dump()["params"].get("variables") or []
            return [EnvVar.model_validate(v) for v in variables]
        return []

    def check_env(self, env: dict[str, str] | None = None, raise_error: bool = True) -> list[EnvVar]:
        env = env or {}
        provider_env = self.env
        required_env = {var.name for var in provider_env if var.required}
        all_env = {var.name for var in provider_env}
        missing_env = [var for var in provider_env if var.name in all_env - env.keys()]
        missing_required_env = [var for var in provider_env if var.name in required_env - env.keys()]
        if missing_required_env and raise_error:
            raise MissingConfigurationError(missing_env=missing_env)
        return missing_env


class ProviderDeploymentState(StrEnum):
    MISSING = "missing"
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"


class ProviderErrorMessage(BaseModel):
    message: str


class ProviderWithState(Provider, extra="allow"):
    state: ProviderDeploymentState | UnmanagedState
    last_error: ProviderErrorMessage | None = None
    missing_configuration: list[EnvVar] = Field(default_factory=list)
