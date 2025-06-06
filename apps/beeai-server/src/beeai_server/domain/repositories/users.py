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

from typing import Protocol, AsyncIterator
from uuid import UUID

from beeai_server.domain.models.user import User


class IUserRepository(Protocol):
    async def list(self) -> AsyncIterator[User]:
        yield ...

    async def create(self, *, user: User) -> None: ...
    async def get(self, *, user_id: UUID) -> User: ...
    async def get_by_email(self, *, email: str) -> User: ...
    async def delete(self, *, user_id: UUID) -> None: ...
