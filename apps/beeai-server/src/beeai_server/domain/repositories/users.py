# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

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
