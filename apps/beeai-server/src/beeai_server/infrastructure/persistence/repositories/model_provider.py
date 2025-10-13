# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Column, DateTime, Row, String, Table, Text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, select

from beeai_server.domain.models.model_provider import ModelCapability, ModelProvider
from beeai_server.domain.repositories.model_provider import IModelProviderRepository
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

model_providers_table = Table(
    "model_providers",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("name", String(1024), nullable=False),
    Column("type", String(128), nullable=False),
    Column("base_url", String(1024), nullable=False, unique=True),  # Unique identifier
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("watsonx_project_id", String(256), nullable=True),
    Column("watsonx_space_id", String(256), nullable=True),
    Column("aws_access_key_id", String(256), nullable=True),
    Column("description", Text, nullable=True),
)


class SqlAlchemyModelProviderRepository(IModelProviderRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, model_provider: ModelProvider) -> None:
        query = model_providers_table.insert().values(
            {
                "id": model_provider.id,
                "name": model_provider.name,
                "type": model_provider.type,
                "base_url": str(model_provider.base_url),
                "created_at": model_provider.created_at,
                "watsonx_project_id": model_provider.watsonx_project_id,
                "watsonx_space_id": model_provider.watsonx_space_id,
                "aws_access_key_id": model_provider.aws_access_key_id,
                "description": model_provider.description,
            }
        )
        try:
            await self.connection.execute(query)
        except IntegrityError as ex:
            raise DuplicateEntityError(
                entity="model_provider", field="base_url", value=str(model_provider.base_url)
            ) from ex

    async def get(self, *, model_provider_id: UUID) -> ModelProvider:
        query = select(model_providers_table).where(model_providers_table.c.id == model_provider_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="model_provider", id=model_provider_id)
        return self._row_to_model_provider(row)

    async def list(self, *, capability: ModelCapability | None = None) -> AsyncIterator[ModelProvider]:
        # Note: capability parameter is kept for interface compatibility but filtering is done in service
        query = select(model_providers_table).order_by(model_providers_table.c.created_at.desc())
        result = await self.connection.execute(query)

        for row in result:
            yield self._row_to_model_provider(row)

    async def delete(self, *, model_provider_id: UUID) -> int:
        query = delete(model_providers_table).where(model_providers_table.c.id == model_provider_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="model_provider", id=model_provider_id)
        return result.rowcount

    def _row_to_model_provider(self, row: Row) -> ModelProvider:
        return ModelProvider(
            id=row.id,
            name=row.name,
            type=row.type,
            base_url=row.base_url,
            created_at=row.created_at,
            watsonx_project_id=row.watsonx_project_id,
            watsonx_space_id=row.watsonx_space_id,
            aws_access_key_id=row.aws_access_key_id,
            description=row.description,
        )
