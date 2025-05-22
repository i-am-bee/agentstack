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
