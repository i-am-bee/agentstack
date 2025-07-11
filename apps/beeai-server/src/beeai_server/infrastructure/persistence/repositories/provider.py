# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import datetime
from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import UUID

from sqlalchemy import JSON, Boolean, Column, Integer, Row, String, Table
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, select

from beeai_server.domain.models.provider import Provider
from beeai_server.domain.repositories.provider import IProviderRepository
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.agent import agent_requests_table, agents_table
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

providers_table = Table(
    "providers",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("source", String(2048), nullable=False),
    Column("registry", String(2048), nullable=True),
    Column("env", JSON, nullable=False),
    Column("auto_stop_timeout_sec", Integer, nullable=False),
    Column("auto_remove", Boolean, default=False, nullable=False),
)


class SqlAlchemyProviderRepository(IProviderRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, provider: Provider) -> None:
        query = providers_table.insert().values(
            {
                "id": provider.id,
                "auto_stop_timeout_sec": int(
                    provider.auto_stop_timeout.total_seconds() if provider.auto_stop_timeout else None
                ),
                "source": str(provider.source.root),
                "registry": provider.registry and str(provider.registry.root),
                "env": [env.model_dump(mode="json") for env in provider.env],
                "auto_remove": provider.auto_remove,
            }
        )
        if provider.auto_remove:
            await self.connection.execute(providers_table.delete().where(providers_table.c.id == provider.id))
        try:
            await self.connection.execute(query)
        except IntegrityError as e:
            # Most likely the name field caused the duplication since it has a unique constraint
            # Extract agent name from the error message if possible
            raise DuplicateEntityError(entity="provider", field="source", value=provider.source.root) from e

    def _to_provider(self, row: Row) -> Provider:
        return Provider.model_validate(
            {
                # ID is determined by source
                "source": row.source,
                "registry": row.registry,
                "auto_stop_timeout": timedelta(seconds=row.auto_stop_timeout_sec),
                "env": row.env,
                "auto_remove": row.auto_remove,
            }
        )

    async def get(self, *, provider_id: UUID) -> Provider:
        query = select(providers_table).where(providers_table.c.id == provider_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="provider", id=provider_id)

        return self._to_provider(row)

    async def delete(self, *, provider_id: UUID) -> None:
        query = delete(providers_table).where(providers_table.c.id == provider_id)
        await self.connection.execute(query)

    async def get_last_active_at(self, *, provider_id: UUID) -> datetime.datetime | None:
        rows = (
            await self.connection.execute(
                agent_requests_table.select()
                .join(agents_table, agent_requests_table.c.agent_id == agents_table.c.id)
                .join(providers_table, agents_table.c.provider_id == providers_table.c.id)
                .where(providers_table.c.id == provider_id)
                .order_by(agent_requests_table.c.finished_at.desc())
                .limit(1)
            )
        ).all()
        if not rows:
            return None
        return rows[0].finished_at or utc_now()

    async def list(self, *, auto_remove_filter: bool | None = None) -> AsyncIterator[Provider]:
        query = providers_table.select()
        if auto_remove_filter is not None:
            query = query.where(providers_table.c.auto_remove == auto_remove_filter)
        async for row in await self.connection.stream(query):
            yield self._to_provider(row)
