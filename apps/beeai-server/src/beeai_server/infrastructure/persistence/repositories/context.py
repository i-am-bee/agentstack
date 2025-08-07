# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from uuid import UUID

from kink import inject
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Row,
    Table,
    delete,
    select,
    update,
)
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.context import Context
from beeai_server.domain.repositories.context import IContextRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
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


@inject
class ContextRepository(IContextRepository):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    async def list(self, user_id: UUID | None = None) -> AsyncIterator[Context]:
        query = select(contexts_table)
        if user_id is not None:
            query = query.where(contexts_table.c.created_by == user_id)

        async for row in await self._connection.stream(query):
            yield self._row_to_context(row)

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
            raise EntityNotFoundError("Context", context_id)
        return self._row_to_context(row)

    async def delete(self, *, context_id: UUID, user_id: UUID | None = None) -> int:
        query = delete(contexts_table).where(contexts_table.c.id == context_id)
        if user_id is not None:
            query = query.where(contexts_table.c.created_by == user_id)

        result = await self._connection.execute(query)
        return result.rowcount

    async def update_last_active(self, *, context_id: UUID) -> None:
        query = update(contexts_table).where(contexts_table.c.id == context_id).values(last_active_at=utc_now())
        await self._connection.execute(query)

    def _row_to_context(self, row: Row) -> Context:
        return Context(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_active_at=row.last_active_at,
            created_by=row.created_by,
            metadata=row.metadata,
        )
