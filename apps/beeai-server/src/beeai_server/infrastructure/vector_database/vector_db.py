# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
from collections import defaultdict
from typing import Iterable, Sequence
from uuid import UUID

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import (
    Table,
    Column,
    MetaData,
    Text,
    Index,
    Row,
    String,
    PrimaryKeyConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as SqlUUID, insert
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.vector_store import VectorStoreItem, VectorStoreDocumentInfo, VectorStoreSearchResult
from beeai_server.domain.repositories.vector_store import IVectorDatabaseRepository
from beeai_server.infrastructure.persistence.repositories.vector_store import (
    vector_store_documents_table,
)

# Common dimensions that we'll support
# From MTEB leaderboard sorted unique dimensions up to 4000:
# https://huggingface.co/spaces/mteb/leaderboard
# len(SUPPORTED_DIMENSIONS) is the upper limit on the number of tables we'll create in the database
SUPPORTED_DIMENSIONS = [64, 128, 256, 312, 384, 512, 768, 896, 1024, 1536, 1792, 2048, 2304, 2560, 3072, 3584, 4000]


metadata = MetaData()


class VectorDatabaseRepository(IVectorDatabaseRepository):
    def __init__(self, connection: AsyncConnection, schema_name: str):
        self.connection = connection
        self.schema_name = schema_name

    def _get_table(self, dimension: int) -> Table:
        table_name = f"collections_dim_{dimension}"
        table_name_with_schema = f"{self.schema_name}.{table_name}"
        if table_name_with_schema in metadata.tables:
            return metadata.tables[table_name_with_schema]
        return Table(
            table_name,
            metadata,
            Column("id", SqlUUID),
            Column("vector_store_id", SqlUUID, nullable=False),
            Column("vector_store_document_id", String(256), nullable=False),
            PrimaryKeyConstraint("id", "vector_store_id"),
            ForeignKeyConstraint(
                ["vector_store_document_id", "vector_store_id"],
                [vector_store_documents_table.c.id, vector_store_documents_table.c.vector_store_id],
                name="fk_collections_to_documents",
                deferrable=True,
                initially="DEFERRED",
                ondelete="CASCADE",
            ),
            Column("text", Text, nullable=False),
            Column("embedding", HALFVEC(dimension), nullable=False),
            Column("metadata", JSONB, nullable=True),
            Index(
                f"{table_name}_vector_index",
                "embedding",
                postgresql_using="hnsw",
                postgresql_with={"m": 16, "ef_construction": 64},
                postgresql_ops={"embedding": "halfvec_l2_ops"},
            ),
            Index(f"{table_name}_vector_store_id_index", "vector_store_id", "vector_store_document_id"),
            schema=self.schema_name,
        )

    def _get_supported_dimension(self, dimension: int) -> int:
        new_dimension = SUPPORTED_DIMENSIONS[0]
        for supported_dim in SUPPORTED_DIMENSIONS:
            if supported_dim > dimension:
                break
            new_dimension = supported_dim
        return new_dimension

    async def create_collection(self, collection_id: UUID, dimension: int):
        supported_dimension = self._get_supported_dimension(dimension)
        table = self._get_table(supported_dimension)
        await self.connection.run_sync(table.create, checkfirst=True)

    async def delete_collection(self, collection_id: UUID, dimension: int):
        supported_dimension = self._get_supported_dimension(dimension)
        table = self._get_table(supported_dimension)
        await table.delete().where(table.c.vector_store_id == collection_id)

    def _get_item_size(self, item: VectorStoreItem) -> int:
        """Approximate size of a single item in bytes."""
        return (
            len(item.id.bytes)
            + len(str(item.document_id).encode("utf-8"))
            + len(item.document_type.encode("utf-8"))
            + len(item.model_id.encode("utf-8"))
            + len(item.text.encode("utf-8"))
            + len(json.dumps(item.metadata).encode("utf-8"))
            + len(item.embedding) * 2
        )

    def estimate_size(self, items: Sequence[VectorStoreItem]) -> list[VectorStoreDocumentInfo]:
        inserted_sizes = defaultdict(int)
        for item in items:
            inserted_sizes[item.document_id] += self._get_item_size(item)
        return [VectorStoreDocumentInfo(id=key, usage_bytes=value) for key, value in inserted_sizes.items()]

    async def add_items(self, collection_id: UUID, items: Sequence[VectorStoreItem]) -> None:
        if not items:
            return
        dimension = len(items[0].embedding)
        supported_dimension = self._get_supported_dimension(dimension)
        table = self._get_table(supported_dimension)

        query = insert(table).values(
            [
                {
                    "id": item.id,
                    "vector_store_id": collection_id,
                    "vector_store_document_id": item.document_id,
                    "embedding": item.embedding,
                    "text": item.text,
                    "metadata": item.metadata,
                }
                for item in items
            ]
        )
        await self.connection.execute(query)

    async def delete_documents(self, collection_id: UUID, dimension: int, vector_store_document_ids: Iterable[str]):
        supported_dimension = self._get_supported_dimension(dimension)
        table = self._get_table(supported_dimension)
        query = table.delete().where(
            (table.c.vector_store_id == collection_id)
            & (table.c.vector_store_document_id.in_(vector_store_document_ids))
        )
        return await self.connection.execute(query)

    def _to_item(self, row: Row) -> VectorStoreItem:
        return VectorStoreItem(
            id=row.id,
            document_id=row.vector_store_document_id,
            embedding=row.embedding.to_list(),
            text=row.text,
            metadata=row.metadata,
        )

    def _to_search_result(self, row: Row) -> VectorStoreSearchResult:
        """Convert a database row to a VectorStoreSearchResult with score."""
        item = self._to_item(row)
        # Convert cosine distance to similarity score (1 - distance)
        score = 1.0 - row.distance
        return VectorStoreSearchResult(item=item, score=score)

    async def similarity_search(
        self,
        collection_id: UUID,
        query_vector: Sequence[float],
        limit: int = 10,
    ) -> Iterable[VectorStoreSearchResult]:
        dimension = len(query_vector)
        supported_dimension = self._get_supported_dimension(dimension)
        table = self._get_table(supported_dimension)

        # Select all columns plus the distance as a named column
        query = (
            table.select()
            .add_columns(table.c.embedding.cosine_distance(query_vector).label("distance"))
            .where(table.c.vector_store_id == collection_id)
            .order_by(table.c.embedding.cosine_distance(query_vector))
            .limit(limit)
        )

        rows = await self.connection.execute(query)
        return [self._to_search_result(row) for row in rows.fetchall()]
