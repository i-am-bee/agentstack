# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import uuid
from collections import defaultdict
from uuid import UUID

from cryptography.fernet import Fernet
from kink import inject
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration
from beeai_server.domain.repositories.env import NOT_SET, EnvStoreEntity, IEnvVariableRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.infrastructure.persistence.repositories.utils import sql_enum
from beeai_server.utils.utils import utc_now

# A polymorphic table for storing environment variables
# This might seem a bit complex but it will make cleaning up easier due to cascading delete.
# Also, the variables are centralized in a single "secrets store", so it can be in theory replaced by
# something like AWS Secrets Manager more easily than storing secrets in each entity


variables_table = Table(
    "variables",
    metadata,
    Column("id", SQL_UUID(as_uuid=True), primary_key=True),
    Column("key", String(256), nullable=False),
    Column("value", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    # Discriminator
    Column("parent_entity", sql_enum(EnvStoreEntity), nullable=False),
    # Foreign key columns
    Column("provider_id", SQL_UUID, ForeignKey("providers.id", ondelete="CASCADE"), nullable=True),
    Column("user_id", SQL_UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    Column("model_provider_id", SQL_UUID, ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=True),
    # Constraints
    CheckConstraint(
        "(provider_id IS NOT NULL)::int + (model_provider_id IS NOT NULL)::int + (user_id IS NOT NULL)::int= 1",
        name="exactly_one_reference",
    ),
    CheckConstraint(
        (
            "(parent_entity = 'provider' AND provider_id IS NOT NULL) OR "
            "(parent_entity = 'model_provider' AND model_provider_id IS NOT NULL) OR"
            "(parent_entity = 'user' AND user_id IS NOT NULL)"
        ),
        name="parent_entity_matches_reference",
    ),
    UniqueConstraint("key", "parent_entity", "provider_id", name="uk_provider"),
    UniqueConstraint("key", "parent_entity", "model_provider_id", name="uk_model_provider"),
    UniqueConstraint("key", "parent_entity", "user_id", name="uk_user"),
    # Indexes
    Index("idx_entity_attributes_provider", "provider_id"),
    Index("idx_entity_attributes_model_provider", "model_provider_id"),
    Index("idx_entity_attributes_user", "user_id"),
)


@inject
class SqlAlchemyEnvVariableRepository(IEnvVariableRepository):
    def __init__(self, connection: AsyncConnection, configuration: Configuration):
        self.connection = connection
        if not configuration.persistence.encryption_key:
            raise RuntimeError("Missing encryption key in configuration.")

        self.fernet = Fernet(configuration.persistence.encryption_key.get_secret_value())

    def _get_parent_column(self, parent_entity: EnvStoreEntity):
        """Get the appropriate foreign key column for the parent entity type."""
        match parent_entity:
            case EnvStoreEntity.PROVIDER:
                return variables_table.c.provider_id
            case EnvStoreEntity.MODEL_PROVIDER:
                return variables_table.c.model_provider_id
            case EnvStoreEntity.USER:
                return variables_table.c.user_id
            case _:
                raise ValueError(f"Unknown parent entity type: {parent_entity}")

    def _parent_filter(self, parent_entity: EnvStoreEntity, parent_entity_id: UUID):
        """Get the filter clause for scoping to a specific parent entity."""
        parent_column = self._get_parent_column(parent_entity)
        return (variables_table.c.parent_entity == parent_entity) & (parent_column == parent_entity_id)

    async def update(
        self,
        *,
        parent_entity: EnvStoreEntity,
        parent_entity_id: UUID,
        variables: dict[str, str | None] | dict[str, str],
    ) -> None:
        if not variables:
            return

        # Get the correct foreign key column for this parent entity
        parent_column = self._get_parent_column(parent_entity)

        # Query existing variables for this entity
        all_entity_variables = variables_table.select().where(self._parent_filter(parent_entity, parent_entity_id))

        existing_keys = {row.key for row in (await self.connection.execute(all_entity_variables)).all()}
        to_remove = [key for key, value in variables.items() if value is None or key in existing_keys]
        crypted = {key: self.fernet.encrypt(var.encode()).decode() for key, var in variables.items() if var is not None}

        if to_remove:
            await self.connection.execute(
                variables_table.delete().where(
                    self._parent_filter(parent_entity, parent_entity_id) & variables_table.c.key.in_(to_remove)
                )
            )

        if crypted:
            await self.connection.execute(
                variables_table.insert().values(
                    [
                        {
                            "id": str(uuid.uuid4()),
                            "key": key,
                            "value": value,
                            "created_at": utc_now(),
                            "parent_entity": parent_entity,
                            parent_column.name: parent_entity_id,
                        }
                        for key, value in crypted.items()
                    ]
                )
            )

    async def get(
        self,
        *,
        parent_entity: EnvStoreEntity,
        parent_entity_id: UUID,
        key: str,
        default: str | None = NOT_SET,  # pyright: ignore [reportArgumentType]
    ) -> str | None:
        query = variables_table.select().where(
            self._parent_filter(parent_entity, parent_entity_id) & (variables_table.c.key == key)
        )
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            if default is NOT_SET:
                raise EntityNotFoundError(entity="variable", id=key)
            return default
        return self.fernet.decrypt(row.value).decode()

    async def get_all(
        self,
        parent_entity: EnvStoreEntity,
        parent_entity_ids: list[UUID],
    ) -> dict[UUID, dict[str, str]]:
        if not parent_entity_ids:
            return {}

        parent_column = self._get_parent_column(parent_entity)

        query = variables_table.select().where(
            (variables_table.c.parent_entity == parent_entity) & parent_column.in_(parent_entity_ids)
        )

        rows = await self.connection.execute(query)

        result = defaultdict(dict)
        for row in rows.all():
            entity_id = getattr(row, parent_column.name)
            result[entity_id][row.key] = self.fernet.decrypt(row.value).decode()

        return result
