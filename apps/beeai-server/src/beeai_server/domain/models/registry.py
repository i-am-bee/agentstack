# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from collections import Counter
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import httpx
import yaml
from anyio import Path
from pydantic import BaseModel, Field, FileUrl, HttpUrl, RootModel, computed_field, field_validator, model_validator

from beeai_server.domain.constants import DEFAULT_AUTO_STOP_TIMEOUT
from beeai_server.utils.github import GithubUrl

if TYPE_CHECKING:
    # Workaround to prevent cyclic imports
    # Models from this file are used in config which is used everywhere throughout the codebase
    from beeai_server.domain.models.provider import ProviderLocation


class ProviderRegistryRecord(BaseModel, extra="allow"):
    location: "ProviderLocation"
    origin: str | None = None
    auto_stop_timeout_sec: int | None = Field(default=int(DEFAULT_AUTO_STOP_TIMEOUT.total_seconds()), ge=0)
    variables: dict[str, str] = {}

    @computed_field
    @property
    def final_origin(self) -> str:
        return self.origin or self.location.origin

    @computed_field
    @property
    def auto_stop_timeout(self) -> timedelta | None:
        return timedelta(seconds=self.auto_stop_timeout_sec) if self.auto_stop_timeout_sec else None

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
    from beeai_server.domain.models.provider import ProviderLocation

    _ = ProviderLocation  # make sure this is imported

    return RegistryManifest.model_validate(content).providers


class NetworkRegistryLocation(RootModel):
    root: HttpUrl

    async def load(self) -> list[ProviderRegistryRecord]:
        async with httpx.AsyncClient(
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        ) as client:
            resp = await client.get(str(self.root))
            return parse_providers_manifest(yaml.safe_load(resp.content))


class GithubRegistryLocation(RootModel):
    root: GithubUrl

    async def load(self) -> list[ProviderRegistryRecord]:
        resolved_url = await self.root.resolve_version()
        url = await resolved_url.get_raw_url()
        network_location = NetworkRegistryLocation(root=HttpUrl(url))
        return await network_location.load()


class FileSystemRegistryLocation(RootModel):
    root: FileUrl

    async def load(self) -> list[ProviderRegistryRecord]:
        content = await Path(self.root.path).read_text()
        return parse_providers_manifest(yaml.safe_load(content))


RegistryLocation = GithubRegistryLocation | NetworkRegistryLocation | FileSystemRegistryLocation
