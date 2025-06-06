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

from typing import runtime_checkable, Protocol, AsyncIterator
from uuid import UUID

from beeai_server.domain.models.file import File, AsyncFile


class IFileRepository(Protocol):
    async def list(self, *, auto_remove_filter: bool | None = None) -> AsyncIterator[File]:
        yield ...

    async def create(self, *, file: File) -> None: ...
    async def total_usage(self, *, user_id: UUID | None = None) -> int: ...
    async def get(self, *, file_id: UUID, user_id: UUID) -> File: ...
    async def delete(self, *, file_id: UUID, user_id: UUID) -> None: ...


@runtime_checkable
class IObjectStorageRepository(Protocol):
    async def upload_file(self, *, file_id: UUID, file: AsyncFile) -> int: ...
    async def get_file(self, *, file_id: UUID) -> AsyncFile: ...
    async def delete_file(self, *, file_id: UUID) -> None: ...
    async def get_file_url(self, *, file_id: UUID) -> str: ...
