# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Any, TYPE_CHECKING

import httpx
import yaml
from anyio import Path
from pydantic import BaseModel, RootModel, FileUrl, HttpUrl

from beeai_server.utils.github import GithubUrl

if TYPE_CHECKING:
    # Workaround to prevent cyclic imports
    # Models from this file are used in config which is used everywhere throughout the codebase
    from beeai_server.domain.models.provider import ProviderLocation


def parse_providers_manifest(content: dict[str, Any]) -> list["ProviderLocation"]:
    from beeai_server.domain.models.provider import ProviderLocation

    class ProviderRegistryRecord(BaseModel, extra="allow"):
        location: ProviderLocation

    class RegistryManifest(BaseModel):
        providers: list[ProviderRegistryRecord]

    return [p.location for p in RegistryManifest.model_validate(content).providers]


class NetworkRegistryLocation(RootModel):
    root: HttpUrl

    async def load(self) -> list["ProviderLocation"]:
        async with httpx.AsyncClient(
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        ) as client:
            resp = await client.get(str(self.root))
            return parse_providers_manifest(yaml.safe_load(resp.content))


class GithubRegistryLocation(RootModel):
    root: GithubUrl

    async def load(self) -> list["ProviderLocation"]:
        resolved_url = await self.root.resolve_version()
        network_location = NetworkRegistryLocation(root=HttpUrl(resolved_url.get_raw_url()))
        return await network_location.load()


class FileSystemRegistryLocation(RootModel):
    root: FileUrl

    async def load(self) -> list["ProviderLocation"]:
        content = await Path(self.root.path).read_text()
        return parse_providers_manifest(yaml.safe_load(content))


RegistryLocation = GithubRegistryLocation | NetworkRegistryLocation | FileSystemRegistryLocation
