# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from enum import StrEnum

from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Row, String, Table
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import select

from beeai_server.domain.models.configuration import SystemConfiguration
from beeai_server.domain.repositories.configurations import IConfigurationsRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata


class ConfigurationType(StrEnum):
    SYSTEM = "system"
    USER = "user"


configurations_table = Table(
    "configurations",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("configuration_type", Enum(ConfigurationType), nullable=False),
    Column("default_llm_model", String(256), nullable=True),
    Column("default_embedding_model", String(256), nullable=True),
    Index(
        "ix_unique_system_configuration",
        "configuration_type",
        unique=True,
        postgresql_where="configuration_type = 'system'",
    ),
)


class SqlAlchemyConfigurationsRepository(IConfigurationsRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def get_system_configuration(self) -> SystemConfiguration:
        query = select(configurations_table).where(
            configurations_table.c.configuration_type == ConfigurationType.SYSTEM
        )
        result = await self.connection.execute(query)

        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="configuration", id="system")

        return self._row_to_system_configuration(row)

    async def create_or_update_system_configuration(self, *, configuration: SystemConfiguration) -> None:
        # Check if system configuration already exists
        query = configurations_table.select().where(
            configurations_table.c.configuration_type == ConfigurationType.SYSTEM
        )
        result = await self.connection.execute(query)
        existing_row = result.fetchone()

        if existing_row:
            # Update existing configuration
            update_stmt = (
                configurations_table.update()
                .where(configurations_table.c.configuration_type == ConfigurationType.SYSTEM)
                .values(
                    default_llm_model=configuration.default_llm_model,
                    default_embedding_model=configuration.default_embedding_model,
                    updated_at=configuration.updated_at,
                    created_by=configuration.created_by,
                )
            )
            await self.connection.execute(update_stmt)
        else:
            # Create new configuration
            insert_stmt = configurations_table.insert().values(
                id=configuration.id,
                configuration_type=ConfigurationType.SYSTEM,
                created_by=configuration.created_by,
                updated_at=configuration.updated_at,
                default_llm_model=configuration.default_llm_model,
                default_embedding_model=configuration.default_embedding_model,
            )
            await self.connection.execute(insert_stmt)

    def _row_to_system_configuration(self, row: Row) -> SystemConfiguration:
        return SystemConfiguration(
            default_llm_model=row.default_llm_model,
            default_embedding_model=row.default_embedding_model,
            updated_at=row.updated_at,
            created_by=row.created_by,
        )
