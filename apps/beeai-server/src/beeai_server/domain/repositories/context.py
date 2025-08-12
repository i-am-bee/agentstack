# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from beeai_server.domain.models.context import Context


class IContextRepository(Protocol):
    async def list(self, user_id: UUID | None = None) -> AsyncIterator[Context]:
        yield ...  # type: ignore

    async def create(self, *, context: Context) -> None: ...
    async def get(self, *, context_id: UUID, user_id: UUID | None = None) -> Context: ...
    async def delete(self, *, context_id: UUID, user_id: UUID | None = None) -> int: ...
    async def update_last_active(self, *, context_id: UUID) -> None: ...
