# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import datetime
from uuid import UUID, uuid4

from kink import inject
from pydantic import TypeAdapter
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Row,
    Table,
    delete,
    select,
    update,
)
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.context import Context, ContextHistoryItem
from beeai_server.domain.repositories.context import IContextRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.infrastructure.persistence.repositories.utils import cursor_paginate
from beeai_server.utils.utils import utc_now

contexts_table = Table(
    "contexts",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_active_at", DateTime(timezone=True), nullable=True),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("metadata", JSON, nullable=True),
)

context_history_table = Table(
    "context_history",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("context_id", ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("history_item", JSON, nullable=False),
    Index("idx_context_history_context_id", "context_id"),
)


@inject
class SqlAlchemyContextRepository(IContextRepository):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    async def list(
        self, user_id: UUID | None = None, last_active_before: datetime | None = None
    ) -> AsyncIterator[Context]:
        yield ...  # type: ignore
        query = select(contexts_table)
        if user_id is not None:
            query = query.where(contexts_table.c.created_by == user_id)

        if last_active_before:
            query = query.where(contexts_table.c.last_active_at < last_active_before)

        async for row in await self._connection.stream(query):
            yield self._row_to_context(row)

    async def list_paginated(
        self,
        user_id: UUID | None = None,
        limit: int = 20,
        after: UUID | None = None,
        order: str = "desc",
        order_by: str = "created_at",
    ) -> PaginatedResult:
        query = contexts_table.select()
        if user_id is not None:
            query = query.where(contexts_table.c.created_by == user_id)

        result = await cursor_paginate(
            connection=self._connection,
            query=query,
            id_column=contexts_table.c.id,
            limit=limit,
            after_cursor=after,
            order=order,
            order_column=getattr(contexts_table.c, order_by),
        )

        return PaginatedResult(
            items=[self._row_to_context(row) for row in result.items],
            total_count=result.total_count,
            has_more=result.has_more,
        )

    async def create(self, *, context: Context) -> None:
        query = contexts_table.insert().values(
            id=context.id,
            created_at=context.created_at,
            updated_at=context.updated_at,
            last_active_at=context.last_active_at,
            created_by=context.created_by,
            metadata=context.metadata,
        )
        await self._connection.execute(query)

    async def get(self, *, context_id: UUID, user_id: UUID | None = None) -> Context:
        query = select(contexts_table).where(contexts_table.c.id == context_id)
        if user_id is not None:
            query = query.where(contexts_table.c.created_by == user_id)

        result = await self._connection.execute(query)
        row = result.fetchone()
        if row is None:
            raise EntityNotFoundError("context", context_id)
        return self._row_to_context(row)

    async def delete(self, *, context_id: UUID, user_id: UUID | None = None) -> int:
        query = delete(contexts_table).where(contexts_table.c.id == context_id)
        if user_id is not None:
            query = query.where(contexts_table.c.created_by == user_id)

        result = await self._connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError("context", context_id)
        return result.rowcount

    async def update_last_active(self, *, context_id: UUID) -> None:
        query = update(contexts_table).where(contexts_table.c.id == context_id).values(last_active_at=utc_now())
        await self._connection.execute(query)

    async def add_history_item(self, *, context_id: UUID, history_item: ContextHistoryItem) -> None:
        adapter = TypeAdapter(ContextHistoryItem)
        query = context_history_table.insert().values(
            id=uuid4(),
            context_id=context_id,
            created_at=utc_now(),
            history_item=adapter.dump_python(history_item),
        )
        await self._connection.execute(query)

    async def list_history(self, *, context_id: UUID) -> AsyncIterator[ContextHistoryItem]:
        adapter = TypeAdapter(ContextHistoryItem)
        query = (
            select(context_history_table.c.history_item)
            .where(context_history_table.c.context_id == context_id)
            .order_by(context_history_table.c.created_at.asc())
        )
        async for row in await self._connection.stream(query):
            yield adapter.validate_python(row.history_item)

    def _row_to_context(self, row: Row) -> Context:
        return Context(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_active_at=row.last_active_at,
            created_by=row.created_by,
            metadata=row.metadata,
        )
