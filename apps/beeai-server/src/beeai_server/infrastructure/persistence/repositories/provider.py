# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, Row, String, Table
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, select

from beeai_server.domain.models.provider import Provider
from beeai_server.domain.repositories.provider import IProviderRepository
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

providers_table = Table(
    "providers",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("source", String(2048), nullable=False),
    Column("registry", String(2048), nullable=True),
    Column("auto_stop_timeout_sec", Integer, nullable=True),
    Column("auto_remove", Boolean, default=False, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_active_at", DateTime(timezone=True), nullable=False),
    Column("agent_card", JSON, nullable=False),
)


class SqlAlchemyProviderRepository(IProviderRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, provider: Provider) -> None:
        query = providers_table.insert().values(self._to_row(provider))
        if provider.auto_remove:
            await self.connection.execute(providers_table.delete().where(providers_table.c.id == provider.id))
        try:
            await self.connection.execute(query)
        except IntegrityError as e:
            raise DuplicateEntityError(entity="provider", field="source", value=str(provider.source.root)) from e

    async def update(self, *, provider: Provider) -> None:
        query = providers_table.update().where(providers_table.c.id == provider.id).values(self._to_row(provider))
        await self.connection.execute(query)

    def _to_row(self, provider: Provider) -> dict[str, Any]:
        return {
            "id": provider.id,
            "auto_stop_timeout_sec": (
                int(provider.auto_stop_timeout.total_seconds()) if provider.auto_stop_timeout else None
            ),
            "source": str(provider.source.root),
            "registry": provider.registry and str(provider.registry.root),
            "auto_remove": provider.auto_remove,
            "agent_card": provider.agent_card.model_dump(mode="json"),
            "created_at": provider.created_at,
            "last_active_at": provider.last_active_at,
        }

    def _to_provider(self, row: Row) -> Provider:
        return Provider.model_validate(
            {
                # ID is determined by source
                "source": row.source,
                "registry": row.registry,
                "auto_stop_timeout": (
                    timedelta(seconds=row.auto_stop_timeout_sec) if row.auto_stop_timeout_sec else None
                ),
                "auto_remove": row.auto_remove,
                "last_active_at": row.last_active_at,
                "created_at": row.created_at,
                "agent_card": row.agent_card,
            }
        )

    async def get(self, *, provider_id: UUID) -> Provider:
        query = select(providers_table).where(providers_table.c.id == provider_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="provider", id=provider_id)

        return self._to_provider(row)

    async def update_last_accessed(self, *, provider_id: UUID) -> None:
        query = providers_table.update().where(providers_table.c.id == provider_id).values(last_active_at=utc_now())
        await self.connection.execute(query)

    async def delete(self, *, provider_id: UUID) -> int:
        query = delete(providers_table).where(providers_table.c.id == provider_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="provider", id=provider_id)
        return result.rowcount

    async def list(self, *, auto_remove_filter: bool | None = None) -> AsyncIterator[Provider]:
        query = providers_table.select()
        if auto_remove_filter is not None:
            query = query.where(providers_table.c.auto_remove == auto_remove_filter)
        async for row in await self.connection.stream(query):
            yield self._to_provider(row)
