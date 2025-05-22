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

from beeai_server.domain.models.provider import Provider


@runtime_checkable
class IProviderRepository(Protocol):
    async def list(self, *, auto_remove_filter: bool | None = None) -> AsyncIterator[Provider]:
        yield ...

    async def create(self, *, provider: Provider) -> None: ...
    async def get(self, *, provider_id: UUID) -> Provider: ...
    async def delete(self, *, provider_id: UUID) -> None: ...
    async def get_last_active_at(self, *, provider_id: UUID) -> None: ...
