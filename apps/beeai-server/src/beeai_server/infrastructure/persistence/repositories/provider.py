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

import datetime
from datetime import timedelta
from typing import AsyncIterator
from uuid import UUID

from sqlalchemy import Table, Column, String, UUID as SqlUUID, Integer, JSON, Row, Boolean
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import select, delete

from beeai_server.domain.models.provider import Provider
from beeai_server.domain.repositories.provider import IProviderRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.agent import agents_table, agent_requests_table
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

providers_table = Table(
    "providers",
    metadata,
    Column("id", SqlUUID, primary_key=True),
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
        await self.connection.execute(query)

    def _to_provider(self, row: Row) -> Provider:
        return Provider.model_validate(
            {
                # ID is determined by source
                "source": row.source,
                "registry": row.registry,
                "auto_stop_timeout": timedelta(seconds=row.auto_stop_timeout_sec),
                "env": row.env,
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
