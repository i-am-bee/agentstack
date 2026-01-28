# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Column, DateTime, ForeignKey, Row, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, select

from agentstack_server.domain.models.provider_discovery import DiscoveryState, ProviderDiscovery
from agentstack_server.domain.repositories.provider_discovery import IProviderDiscoveryRepository
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.infrastructure.persistence.repositories.db_metadata import metadata
from agentstack_server.infrastructure.persistence.repositories.utils import sql_enum

provider_discoveries_table = Table(
    "provider_discoveries",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("status", sql_enum(DiscoveryState), nullable=False),
    Column("docker_image", String(2048), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("agent_card", JSONB, nullable=True),
    Column("error_message", String, nullable=True),
)


class SqlAlchemyProviderDiscoveryRepository(IProviderDiscoveryRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, discovery: ProviderDiscovery) -> None:
        query = provider_discoveries_table.insert().values(self._to_row(discovery))
        await self.connection.execute(query)

    async def get(self, *, discovery_id: UUID, user_id: UUID | None = None) -> ProviderDiscovery:
        query = select(provider_discoveries_table).where(provider_discoveries_table.c.id == discovery_id)
        if user_id is not None:
            query = query.where(provider_discoveries_table.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="provider_discovery", id=discovery_id)
        return self._to_discovery(row)

    async def update(self, *, discovery: ProviderDiscovery) -> None:
        query = (
            provider_discoveries_table.update()
            .where(provider_discoveries_table.c.id == discovery.id)
            .values(self._to_row(discovery))
        )
        await self.connection.execute(query)

    async def delete(self, *, discovery_id: UUID, user_id: UUID | None = None) -> int:
        query = delete(provider_discoveries_table).where(provider_discoveries_table.c.id == discovery_id)
        if user_id is not None:
            query = query.where(provider_discoveries_table.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="provider_discovery", id=discovery_id)
        return result.rowcount

    async def delete_older_than(self, *, older_than: datetime) -> int:
        query = delete(provider_discoveries_table).where(provider_discoveries_table.c.created_at < older_than)
        result = await self.connection.execute(query)
        return result.rowcount

    async def list(
        self, *, user_id: UUID | None = None, status: DiscoveryState | None = None
    ) -> AsyncIterator[ProviderDiscovery]:
        query = select(provider_discoveries_table)
        if user_id is not None:
            query = query.where(provider_discoveries_table.c.created_by == user_id)
        if status is not None:
            query = query.where(provider_discoveries_table.c.status == status)
        async for row in await self.connection.stream(query):
            yield self._to_discovery(row)

    def _to_row(self, discovery: ProviderDiscovery) -> dict[str, Any]:
        return {
            "id": discovery.id,
            "created_at": discovery.created_at,
            "status": discovery.status,
            "docker_image": discovery.docker_image,
            "created_by": discovery.created_by,
            "agent_card": discovery.agent_card.model_dump(mode="json") if discovery.agent_card else None,
            "error_message": discovery.error_message,
        }

    def _to_discovery(self, row: Row) -> ProviderDiscovery:
        return ProviderDiscovery.model_validate(
            {
                "id": row.id,
                "created_at": row.created_at,
                "status": row.status,
                "docker_image": row.docker_image,
                "created_by": row.created_by,
                "agent_card": row.agent_card,
                "error_message": row.error_message,
            }
        )
