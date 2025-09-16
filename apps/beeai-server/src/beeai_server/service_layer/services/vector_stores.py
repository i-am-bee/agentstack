# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import builtins
import logging
from collections.abc import Iterable
from uuid import UUID

from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.domain.models.user import User
from beeai_server.domain.models.vector_store import (
    DocumentType,
    VectorStore,
    VectorStoreDocument,
    VectorStoreItem,
    VectorStoreSearchResult,
)
from beeai_server.exceptions import InvalidVectorDimensionError, StorageCapacityExceededError
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class VectorStoreService:
    """Service for managing vector stores."""

    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration):
        self._uow = uow
        self._storage_limit_per_user = configuration.vector_stores.storage_limit_per_user_bytes

    async def list(self, *, user: User) -> list[VectorStore]:
        """List all vector stores for a user."""
        async with self._uow() as uow:
            return [document async for document in uow.vector_stores.list(user_id=user.id)]

    async def create(
        self, *, name: str, dimension: int, model_id: str, user: User, context_id: UUID | None = None
    ) -> VectorStore:
        vector_store = VectorStore(
            name=name, dimension=dimension, created_by=user.id, model_id=model_id, context_id=context_id
        )
        async with self._uow() as uow:
            await uow.vector_stores.create(vector_store=vector_store)
            await uow.vector_database.create_collection(collection_id=vector_store.id, dimension=dimension)
            await uow.commit()
        return vector_store

    async def get(self, *, vector_store_id: UUID, user: User, context_id: UUID | None = None) -> VectorStore:
        """Get a vector store by ID."""
        async with self._uow() as uow:
            vector_store = await uow.vector_stores.get(
                vector_store_id=vector_store_id, user_id=user.id, context_id=context_id
            )
            await uow.vector_stores.update_last_accessed(vector_store_ids={vector_store_id})
            await uow.commit()
            return vector_store

    async def delete(self, *, vector_store_id: UUID, user: User, context_id: UUID | None = None) -> None:
        """Delete a vector store by ID."""
        async with self._uow() as uow:
            await uow.vector_stores.delete(vector_store_id=vector_store_id, user_id=user.id, context_id=context_id)
            # Records in vector_database are deleted automatically by CASCADE operations in postgres
            await uow.commit()

    async def list_documents(
        self, *, vector_store_id: UUID, user: User, context_id: UUID | None = None
    ) -> builtins.list[VectorStoreDocument]:
        """List all documents in a vector store."""
        async with self._uow() as uow:
            # check ownership
            await uow.vector_stores.get(vector_store_id=vector_store_id, user_id=user.id, context_id=context_id)
            return [document async for document in uow.vector_stores.list_documents(vector_store_id=vector_store_id)]

    async def remove_documents(
        self, *, vector_store_id: UUID, document_ids: Iterable[str], user: User, context_id: UUID | None = None
    ) -> None:
        async with self._uow() as uow:
            # check ownership
            await uow.vector_stores.get(vector_store_id=vector_store_id, user_id=user.id, context_id=context_id)
            await uow.vector_stores.remove_documents(vector_store_id=vector_store_id, document_ids=document_ids)
            # Records in vector_database are deleted automatically by CASCADE operations in postgres
            await uow.commit()

    async def add_items(
        self,
        *,
        vector_store_id: UUID,
        items: builtins.list[VectorStoreItem],
        user: User,
        context_id: UUID | None = None,
    ) -> None:
        async with self._uow() as uow:
            # Verify the user owns the vector store
            vector_store = await uow.vector_stores.get(
                vector_store_id=vector_store_id, user_id=user.id, context_id=context_id
            )

            # Check dimension
            if any(len(item.embedding) != vector_store.dimension for item in items):
                raise InvalidVectorDimensionError(
                    f"Vector dimensions must match vector store dimension: {vector_store.dimension}"
                )

            # Check usage
            usage_bytes_per_document_id = {d.id: d.usage_bytes for d in uow.vector_database.estimate_size(items)}
            total_usage = await uow.vector_stores.total_usage(user_id=user.id)
            if total_usage + sum(usage_bytes_per_document_id.values()) > self._storage_limit_per_user:
                # We are a bit more cautious here, the storage may in fact not be exceeded because some documents
                # or items might already be in the database - the operation below is an upsert, but for simplicity
                # we check the usage as if all items were new.
                raise StorageCapacityExceededError(entity="vector_store", max_size=self._storage_limit_per_user)

            await uow.vector_stores.upsert_documents(
                documents={
                    item.document_id: VectorStoreDocument(
                        vector_store_id=vector_store_id,
                        id=item.document_id,
                        file_id=UUID(item.document_id) if item.document_type == DocumentType.PLATFORM_FILE else None,
                        usage_bytes=usage_bytes_per_document_id.get(item.document_id),
                    )
                    for item in items
                }.values()
            )
            await uow.vector_database.add_items(collection_id=vector_store_id, items=items)
            await uow.commit()

    async def search(
        self,
        *,
        vector_store_id: UUID,
        query_vector: builtins.list[float],
        limit: int = 10,
        user: User,
        context_id: UUID | None = None,
    ) -> builtins.list[VectorStoreSearchResult]:
        """
        Search a vector store using a query vector and return results with similarity scores.
        """
        async with self._uow() as uow:
            await uow.vector_stores.get(vector_store_id=vector_store_id, user_id=user.id, context_id=context_id)
            results = await uow.vector_database.similarity_search(
                collection_id=vector_store_id, query_vector=query_vector, limit=limit
            )
            return list(results)
