# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Protocol
from uuid import UUID

from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.context import Context, ContextHistoryItem


class IContextRepository(Protocol):
    async def list(
        self, user_id: UUID | None = None, last_active_before: datetime | None = None
    ) -> AsyncIterator[Context]:
        yield ...  # type: ignore

    async def list_paginated(
        self,
        user_id: UUID | None = None,
        limit: int = 20,
        page_token: UUID | None = None,
        order: str = "desc",
        order_by: str = "created_at",
    ) -> PaginatedResult: ...

    async def create(self, *, context: Context) -> None: ...
    async def get(self, *, context_id: UUID, user_id: UUID | None = None) -> Context: ...
    async def delete(self, *, context_id: UUID, user_id: UUID | None = None) -> int: ...
    async def update_last_active(self, *, context_id: UUID) -> None: ...
    async def add_history_item(self, *, context_id: UUID, history_item: ContextHistoryItem) -> None: ...
    async def list_history(
        self,
        *,
        context_id: UUID,
        page_token: UUID | None = None,
        limit: int = 20,
        order_by: str = "created_at",
        order="desc",
    ) -> PaginatedResult[ContextHistoryItem]: ...
