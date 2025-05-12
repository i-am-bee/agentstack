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

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Iterable, Protocol, runtime_checkable, AsyncIterator

from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.github import ResolvedGithubUrl
from beeai_server.utils.logs_container import LogsContainer
from pydantic import BaseModel

if TYPE_CHECKING:
    from beeai_server.domain.provider.model import BaseProvider

NOT_SET = object()


@runtime_checkable
class IProviderRepository(Protocol):
    async def sync(self) -> None: ...
    async def list(self) -> list["BaseProvider"]: ...
    async def create(self, *, provider: "BaseProvider") -> None: ...
    async def get(self, *, provider_id: str) -> "BaseProvider": ...
    async def delete(self, *, provider_id: str) -> None: ...


class IEnvVariableRepository(Protocol):
    async def sync(self) -> None: ...
    async def get(self, key: str, default: str | None = NOT_SET) -> str: ...
    async def get_all(self) -> dict[str, str]: ...
    async def update(self, update: dict[str, str | None]) -> None: ...


class IContainerBackend(Protocol):
    async def import_image(self, *, data: AsyncIterator[bytes], image_id: DockerImageID) -> None: ...
    async def build_from_github(
        self, *, github_url: ResolvedGithubUrl, destination: DockerImageID | None = None, logs_container: LogsContainer
    ) -> DockerImageID: ...
    async def delete_image(self, *, image: DockerImageID): ...
    async def pull_image(
        self, *, image: DockerImageID, logs_container: LogsContainer | None = None, force: bool = False
    ): ...
    async def check_image(self, *, image: DockerImageID | str) -> bool: ...
    async def extract_labels(self, *, image: DockerImageID) -> dict[str, str]: ...

    @asynccontextmanager
    async def open_container(
        self,
        *,
        image: DockerImageID,
        name: str | None = None,
        command: list[str] | None = None,
        volumes: Iterable[str] | None = None,
        env: dict[str, str] | None = None,
        port_mappings: dict[str, str] | None = None,
        logs_container: LogsContainer | None = None,
        restart: str | None = None,
    ): ...


class TelemetryConfig(BaseModel):
    sharing_enabled: bool = True


@runtime_checkable
class ITelemetryRepository(Protocol):
    async def sync(self) -> None: ...
    async def set(self, *, config: TelemetryConfig) -> None: ...
    async def get(self) -> TelemetryConfig: ...
