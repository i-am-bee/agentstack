# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Row, String, Table
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, select

from agentstack_server.domain.models.provider import Provider, ProviderType, UnmanagedState
from agentstack_server.domain.repositories.provider import IProviderRepository
from agentstack_server.exceptions import DuplicateEntityError, EntityNotFoundError
from agentstack_server.infrastructure.persistence.repositories.db_metadata import metadata
from agentstack_server.infrastructure.persistence.repositories.utils import sql_enum
from agentstack_server.utils.utils import utc_now

providers_table = Table(
    "providers",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("type", sql_enum(ProviderType), nullable=False),
    Column("source", String(2048), nullable=False, unique=True),
    Column("origin", String(2048), nullable=False),
    Column("version_info", JSON, nullable=False),
    Column("registry", String(2048), nullable=True),
    Column("auto_stop_timeout_sec", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("last_active_at", DateTime(timezone=True), nullable=False),
    Column("agent_card", JSON, nullable=False),
    Column("unmanaged_state", sql_enum(UnmanagedState), nullable=True),
)


class SqlAlchemyProviderRepository(IProviderRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, provider: Provider) -> None:
        provider_row = self._to_row(provider)
        query = providers_table.insert().values(provider_row)
        try:
            await self.connection.execute(query)
        except IntegrityError as e:
            raise DuplicateEntityError(entity="provider", field="source", value=str(provider.source.root)) from e

    async def update_unmanaged_state(self, provider_id: UUID, state: UnmanagedState) -> None:
        query = providers_table.update().where(providers_table.c.id == provider_id).values(unmanaged_state=state)
        await self.connection.execute(query)

    async def update(self, *, provider: Provider) -> None:
        query = providers_table.update().where(providers_table.c.id == provider.id).values(self._to_row(provider))
        await self.connection.execute(query)

    def _to_row(self, provider: Provider) -> dict[str, Any]:
        return {
            "id": provider.id,
            "auto_stop_timeout_sec": provider.auto_stop_timeout.total_seconds(),
            "type": provider.type,
            "source": str(provider.source.root),
            "origin": provider.origin,
            "version_info": provider.version_info.model_dump(mode="json"),
            "registry": provider.registry and str(provider.registry.root),
            "agent_card": provider.agent_card.model_dump(mode="json"),
            "created_at": provider.created_at,
            "updated_at": provider.updated_at,
            "created_by": provider.created_by,
            "last_active_at": provider.last_active_at,
            "unmanaged_state": provider.unmanaged_state,
        }

    def _to_provider(self, row: Row) -> Provider:
        return Provider.model_validate(
            {
                "id": row.id,
                "source": row.source,
                "origin": row.origin,
                # "type": row.type, # type is determined dynamically from source (but we store it for filtering)
                "version_info": row.version_info,
                "registry": row.registry,
                "auto_stop_timeout": timedelta(seconds=row.auto_stop_timeout_sec),
                "last_active_at": row.last_active_at,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "created_by": row.created_by,
                "agent_card": row.agent_card,
                "unmanaged_state": row.unmanaged_state,
            }
        )

    async def get(self, *, provider_id: UUID, user_id: UUID | None = None) -> Provider:
        query = select(providers_table).where(providers_table.c.id == provider_id)
        if user_id is not None:
            query = query.where(providers_table.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="provider", id=provider_id)

        return self._to_provider(row)

    async def update_last_accessed(self, *, provider_id: UUID) -> None:
        query = providers_table.update().where(providers_table.c.id == provider_id).values(last_active_at=utc_now())
        await self.connection.execute(query)

    async def delete(self, *, provider_id: UUID, user_id: UUID | None = None) -> int:
        query = delete(providers_table).where(providers_table.c.id == provider_id)
        if user_id is not None:
            query = query.where(providers_table.c.created_by == user_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="provider", id=provider_id)
        return result.rowcount

    async def list(
        self,
        *,
        type: ProviderType | None = None,
        user_id: UUID | None = None,
        exclude_user_id: UUID | None = None,
        origin: str | None = None,
    ) -> AsyncIterator[Provider]:
        query = providers_table.select()
        if user_id is not None:
            query = query.where(providers_table.c.created_by == user_id)
        if exclude_user_id is not None:
            query = query.where(providers_table.c.created_by != exclude_user_id)
        if origin is not None:
            query = query.where(providers_table.c.origin == origin)
        if type is not None:
            query = query.where(providers_table.c.type == type)
        async for row in await self.connection.stream(query):
            yield self._to_provider(row)
