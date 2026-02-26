# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import httpx
import yaml
from anyio import Path
from pydantic import BaseModel, Field, FileUrl, HttpUrl, RootModel, field_validator, model_validator

from agentstack_server.domain.constants import DEFAULT_AUTO_STOP_TIMEOUT
from agentstack_server.exceptions import VersionResolveError
from agentstack_server.utils.github import GithubUrl

__all__ = [
    "FileSystemModelProviderRegistryLocation",
    "FileSystemRegistryLocation",
    "GithubRegistryLocation",
    "ModelProviderRegistryLocation",
    "ModelProviderRegistryManifest",
    "ModelProviderRegistryRecord",
    "NetworkRegistryLocation",
    "ProviderRegistryRecord",
    "RegistryLocation",
    "RegistryManifest",
    "parse_model_providers_manifest",
    "parse_providers_manifest",
]

if TYPE_CHECKING:
    # Workaround to prevent cyclic imports
    # Models from this file are used in config which is used everywhere throughout the codebase
    from agentstack_server.domain.models.model_provider import ModelProviderType
    from agentstack_server.domain.models.provider import ProviderLocation


class ProviderRegistryRecord(BaseModel, extra="allow"):
    location: ProviderLocation
    origin: str = Field(default_factory=lambda data: data["location"].origin)
    auto_stop_timeout_sec: int = Field(
        default=int(DEFAULT_AUTO_STOP_TIMEOUT.total_seconds()),
        ge=0,
        description="Downscale after this many seconds of inactivity. Set to 0 to disable downscaling.",
    )
    variables: dict[str, str] = {}

    @property
    def auto_stop_timeout(self) -> timedelta:
        return timedelta(seconds=self.auto_stop_timeout_sec)

    @field_validator("variables", mode="before")
    @classmethod
    def convert_variables_to_str(cls, v: Any | None):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("env must be a dictionary")
        return {str(k): str(v) for k, v in v.items()}


class RegistryManifest(BaseModel):
    providers: list[ProviderRegistryRecord]

    @model_validator(mode="after")
    def unique_origin(self):
        origin_counts = Counter(p.origin for p in self.providers if p.origin is not None)
        assert all(count == 1 for count in origin_counts.values()), (
            f"Registry origins must be unique: {origin_counts.most_common()}"
        )
        return self


def parse_providers_manifest(content: dict[str, Any]) -> list[ProviderRegistryRecord]:
    from agentstack_server.domain.models.provider import ProviderLocation

    _ = ProviderLocation  # make sure this is imported

    return RegistryManifest.model_validate(content).providers


class NetworkRegistryLocation(RootModel[HttpUrl]):
    root: HttpUrl

    async def load(self) -> list[ProviderRegistryRecord]:
        async with httpx.AsyncClient(
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        ) as client:
            resp = await client.get(str(self.root))
            return parse_providers_manifest(yaml.safe_load(resp.content))


class GithubRegistryLocation(RootModel[GithubUrl]):
    root: GithubUrl

    async def load(self) -> list[ProviderRegistryRecord]:
        try:
            resolved_url = await self.root.resolve_version()
        except Exception as ex:
            raise VersionResolveError(str(self.root), str(ex)) from ex
        url = await resolved_url.get_raw_url()
        network_location = NetworkRegistryLocation(root=HttpUrl(url))
        return await network_location.load()


class FileSystemRegistryLocation(RootModel[FileUrl]):
    root: FileUrl

    async def load(self) -> list[ProviderRegistryRecord]:
        if self.root.path is None:
            return []
        content = await Path(self.root.path).read_text()
        return parse_providers_manifest(yaml.safe_load(content))


RegistryLocation = GithubRegistryLocation | NetworkRegistryLocation | FileSystemRegistryLocation


class ModelProviderRegistryRecord(BaseModel, extra="allow"):
    name: str | None = None
    description: str | None = None
    type: ModelProviderType
    base_url: HttpUrl
    api_key: str
    watsonx_project_id: str | None = None
    watsonx_space_id: str | None = None


class ModelProviderRegistryManifest(BaseModel):
    providers: list[ModelProviderRegistryRecord]


def parse_model_providers_manifest(content: dict[str, Any]) -> list[ModelProviderRegistryRecord]:
    from agentstack_server.domain.models.model_provider import ModelProviderType

    _ = ModelProviderType  # make sure this is imported

    return ModelProviderRegistryManifest.model_validate(content).providers


class FileSystemModelProviderRegistryLocation(RootModel[FileUrl]):
    root: FileUrl

    async def load(self) -> list[ModelProviderRegistryRecord]:
        if self.root.path is None:
            return []
        content = await Path(self.root.path).read_text()
        return parse_model_providers_manifest(yaml.safe_load(content))


ModelProviderRegistryLocation = FileSystemModelProviderRegistryLocation
