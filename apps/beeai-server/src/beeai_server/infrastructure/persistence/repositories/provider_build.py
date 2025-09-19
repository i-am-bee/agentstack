# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Row, String, Table
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import select

from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.provider_build import BuildState, ProviderBuild
from beeai_server.domain.repositories.provider_build import IProviderBuildRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.infrastructure.persistence.repositories.utils import cursor_paginate, sql_enum

provider_builds_table = Table(
    "provider_builds",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("source", JSON, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    # The CASCADE might leave some k8s jobs orphaned without cancellation, but jobs have timeout and self-deletion
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    Column("status", sql_enum(BuildState), nullable=False),
    Column("destination", String(512), nullable=False),
)


class SqlAlchemyProviderBuildRepository(IProviderBuildRepository):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    async def create(self, *, provider_build: ProviderBuild) -> None:
        query = provider_builds_table.insert().values(self._to_row(provider_build))
        await self._connection.execute(query)

    async def update(self, *, provider_build: ProviderBuild) -> None:
        query = (
            provider_builds_table.update()
            .where(provider_builds_table.c.id == provider_build.id)
            .values(self._to_row(provider_build))
        )
        await self._connection.execute(query)

    def _to_row(self, provider_build: ProviderBuild) -> dict[str, Any]:
        return {
            "id": provider_build.id,
            "source": provider_build.source.model_dump(mode="json"),
            "created_at": provider_build.created_at,
            "status": provider_build.status,
            "created_by": provider_build.created_by,
            "destination": str(provider_build.destination),
        }

    def _to_provider_build(self, row: Row) -> ProviderBuild:
        return ProviderBuild.model_validate(
            {
                "id": row.id,
                "source": row.source,
                "destination": row.destination,
                "created_at": row.created_at,
                "created_by": row.created_by,
                "status": row.status,
            }
        )

    async def get(self, *, provider_build_id: UUID) -> ProviderBuild:
        query = select(provider_builds_table).where(provider_builds_table.c.id == provider_build_id)
        result = await self._connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="provider_build", id=provider_build_id)
        return self._to_provider_build(row)

    async def delete(self, *, provider_build_id: UUID) -> int:
        query = provider_builds_table.delete().where(provider_builds_table.c.id == provider_build_id)
        result = await self._connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError("provider_build", provider_build_id)
        return result.rowcount

    async def list(self, *, status: BuildState | None = None) -> AsyncIterator[ProviderBuild]:
        query = provider_builds_table.select()
        if status is not None:
            query = query.where(provider_builds_table.c.status == status)
        async for row in await self._connection.stream(query):
            yield self._to_provider_build(row)

    async def list_paginated(
        self,
        *,
        limit: int = 20,
        page_token: UUID | None = None,
        order: str = "desc",
        order_by: str = "created_at",
        status: BuildState | None = None,
    ) -> PaginatedResult[ProviderBuild]:
        query = provider_builds_table.select()
        if status is not None:
            query = query.where(provider_builds_table.c.status == status)

        result = await cursor_paginate(
            connection=self._connection,
            query=query,
            id_column=provider_builds_table.c.id,
            limit=limit,
            after_cursor=page_token,
            order=order,
            order_column=getattr(provider_builds_table.c, order_by),
        )

        return PaginatedResult(
            items=[self._to_provider_build(row) for row in result.items],
            total_count=result.total_count,
            has_more=result.has_more,
        )
