# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from typing import AsyncIterator, Iterable
from uuid import UUID

from kink import inject
from sqlalchemy import (
    Table,
    Column,
    String,
    DateTime,
    Row,
    select,
    UUID as SqlUUID,
    ForeignKey,
    Integer,
    func,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.vector_store import VectorStore, VectorStoreDocument
from beeai_server.domain.repositories.vector_store import IVectorStoreRepository
from beeai_server.exceptions import EntityNotFoundError, DuplicateEntityError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

# Main table for vector stores
vector_stores_table = Table(
    "vector_stores",
    metadata,
    Column("id", SqlUUID, primary_key=True),
    Column("name", String(256), nullable=True),
    Column("model_id", String(256), nullable=False),
    Column("dimension", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_active_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
)

vector_store_documents_table = Table(
    "vector_store_documents",
    metadata,
    Column("id", String(256)),
    Column("vector_store_id", ForeignKey("vector_stores.id", ondelete="CASCADE"), nullable=False),
    Column("usage_bytes", Integer, nullable=True),
    Column("file_id", ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    PrimaryKeyConstraint("id", "vector_store_id", name="vector_store_documents_pk"),
)


@inject
class SqlAlchemyVectorStoreRepository(IVectorStoreRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    def _to_vector_store(self, row: Row) -> VectorStore:
        data = {
            "id": row.id,
            "name": row.name,
            "model_id": row.model_id,
            "dimension": row.dimension,
            "created_at": row.created_at,
            "last_active_at": row.last_active_at,
            "created_by": row.created_by,
            "stats": {
                "usage_bytes": row.total_usage_bytes,
                "num_documents": row.num_documents,
            },
        }
        return VectorStore.model_validate(data)

    def _to_vector_store_document(self, row: Row) -> VectorStoreDocument:
        return VectorStoreDocument.model_validate(
            {
                "id": row.id,
                "vector_store_id": row.vector_store_id,
                "file_id": row.file_id,
                "usage_bytes": row.usage_bytes,
                "created_at": row.created_at,
            }
        )

    async def create(self, *, vector_store: VectorStore) -> VectorStore:
        query = vector_stores_table.insert().values(
            id=vector_store.id,
            model_id=vector_store.model_id,
            name=vector_store.name,
            dimension=vector_store.dimension,
            created_at=vector_store.created_at,
            last_active_at=vector_store.last_active_at,
            created_by=vector_store.created_by,
        )
        await self.connection.execute(query)

    async def list(self, *, user_id: UUID | None = None) -> AsyncIterator[VectorStore]:
        query = select(
            vector_stores_table,
            func.coalesce(func.sum(vector_store_documents_table.c.usage_bytes), 0).label("total_usage_bytes"),
            func.coalesce(func.count(vector_store_documents_table.c.id), 0).label("num_documents"),
        ).outerjoin(
            vector_store_documents_table,
            vector_stores_table.c.id == vector_store_documents_table.c.vector_store_id,
        )

        if user_id:
            query = query.where(vector_stores_table.c.created_by == user_id)

        # Group by all columns of the vector_stores_table to collapse the joined rows
        query = query.group_by(*vector_stores_table.c)

        async for row in await self.connection.stream(query):
            yield self._to_vector_store(row)

    async def get(self, *, vector_store_id: UUID, user_id: UUID | None = None) -> VectorStore:
        # Select all columns from the main table
        query = (
            select(
                vector_stores_table,
                func.coalesce(func.sum(vector_store_documents_table.c.usage_bytes), 0).label("total_usage_bytes"),
                func.coalesce(func.count(vector_store_documents_table.c.id), 0).label("num_documents"),
            )
            .outerjoin(
                vector_store_documents_table,
                vector_stores_table.c.id == vector_store_documents_table.c.vector_store_id,
            )
            .where(vector_stores_table.c.id == vector_store_id)
        )

        if user_id:
            query = query.where(vector_stores_table.c.created_by == user_id)

        # Group by all columns of the vector_stores_table to collapse the joined rows
        query = query.group_by(*vector_stores_table.c)

        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="vector_store", id=vector_store_id)

        return self._to_vector_store(row)

    async def delete(self, *, vector_store_id: UUID, user_id: UUID | None = None) -> None:
        query = vector_stores_table.delete().where(vector_stores_table.c.id == vector_store_id)

        if user_id:
            query = query.where(vector_stores_table.c.created_by == user_id)

        await self.connection.execute(query)

    async def update_last_accessed(self, *, vector_store_ids: Iterable[UUID]) -> None:
        query = (
            vector_stores_table.update()
            .where(vector_stores_table.c.id.in_(vector_store_ids))
            .values(last_active_at=utc_now())
        )
        await self.connection.execute(query)

    async def upsert_documents(self, *, documents: Iterable[VectorStoreDocument]) -> None:
        # Update the last accessed timestamp
        query = insert(vector_store_documents_table).values(
            [
                {
                    "id": document.id,
                    "vector_store_id": document.vector_store_id,
                    "file_id": document.file_id,
                    "usage_bytes": document.usage_bytes,
                    "created_at": document.created_at,
                }
                for document in documents
            ]
        )
        try:
            query = query.on_conflict_do_update(
                index_elements=["id", "vector_store_id"],
                set_={
                    # The column to update is 'usage_bytes'.
                    "usage_bytes": (
                        # Get the existing value from the row in the table (table.c.column)
                        vector_store_documents_table.c.usage_bytes
                        +
                        # Get the new value from the data we TRIED to insert (statement.excluded.column)
                        query.excluded.usage_bytes
                    )
                },
            )
            await self.connection.execute(query)
        except IntegrityError:
            raise DuplicateEntityError(entity="vector_store_document", field="id", value=str({d.id for d in documents}))
        await self.update_last_accessed(vector_store_ids={d.vector_store_id for d in documents})

    async def total_usage(self, *, user_id: UUID | None = None) -> int:
        query = select(func.coalesce(func.sum(vector_store_documents_table.c.usage_bytes), 0))
        if user_id:
            query = query.join(vector_stores_table.c.id == vector_store_documents_table.c.vector_store_id).where(
                vector_store_documents_table.c.created_by == user_id
            )
        return await self.connection.scalar(query)

    async def list_documents(
        self, *, vector_store_id: UUID, user_id: UUID | None = None
    ) -> AsyncIterator[VectorStoreDocument]:
        query = select(vector_store_documents_table).where(
            vector_store_documents_table.c.vector_store_id == vector_store_id
        )
        if user_id:
            query = query.join(
                vector_stores_table, vector_stores_table.c.id == vector_store_documents_table.c.vector_store_id
            ).where(vector_stores_table.c.created_by == user_id)

        async for row in await self.connection.stream(query):
            yield self._to_vector_store_document(row)

    async def remove_documents(
        self, *, vector_store_id: UUID, document_ids: Iterable[str], user_id: UUID | None = None
    ) -> int:
        query = vector_store_documents_table.delete().where(
            (vector_store_documents_table.c.vector_store_id == vector_store_id)
            & (vector_store_documents_table.c.id.in_(document_ids))
        )

        if user_id:
            query = query.where(
                vector_store_documents_table.c.vector_store_id.in_(
                    select(vector_stores_table.c.id).where(vector_stores_table.c.created_by == user_id)
                )
            )
        result = await self.connection.execute(query)
        return result.rowcount

    async def delete_expired(self, *, active_threshold: timedelta) -> int:
        # Calculate the expiration date
        expiration_date = utc_now() - active_threshold
        query = vector_stores_table.delete().where(vector_stores_table.c.last_active_at < expiration_date)
        result = await self.connection.execute(query)
        return result.rowcount
