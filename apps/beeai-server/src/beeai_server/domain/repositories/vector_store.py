# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator, Iterable, Sequence
from datetime import timedelta
from typing import Protocol
from uuid import UUID

from beeai_server.domain.models.vector_store import (
    VectorStore,
    VectorStoreDocument,
    VectorStoreDocumentInfo,
    VectorStoreItem,
    VectorStoreSearchResult,
)


class IVectorStoreRepository(Protocol):
    """Interface for vector store repository operations."""

    async def list(self, *, user_id: UUID | None = None) -> AsyncIterator[VectorStore]:
        yield

    async def create(self, *, vector_store: VectorStore) -> None: ...
    async def get(self, *, vector_store_id: UUID, user_id: UUID | None = None) -> VectorStore: ...
    async def delete(self, *, vector_store_id: UUID, user_id: UUID | None = None) -> None: ...
    async def update_last_accessed(self, *, vector_store_ids: Iterable[UUID]) -> None: ...
    async def upsert_documents(self, *, documents: Iterable[VectorStoreDocument]) -> None: ...
    async def list_documents(self, *, vector_store_id: UUID, user_id: UUID | None = None):
        yield

    async def remove_documents(
        self, *, vector_store_id: UUID, document_ids: Iterable[str], user_id: UUID | None = None
    ) -> int: ...
    async def delete_expired(self, *, active_threshold: timedelta) -> int: ...


class IVectorDatabaseRepository(Protocol):
    async def create_collection(self, collection_id: UUID, dimension: int): ...
    async def delete_collection(self, collection_id: UUID, dimension: int): ...
    async def add_items(self, collection_id: UUID, items: Sequence[VectorStoreItem]) -> None: ...
    def estimate_size(self, items: Sequence[VectorStoreItem]) -> list[VectorStoreDocumentInfo]: ...
    async def delete_documents(self, collection_id: UUID, dimension: int, document_ids: Iterable[str]): ...
    async def similarity_search(
        self, collection_id: UUID, query_vector: Sequence[float], limit: int = 10
    ) -> Iterable[VectorStoreSearchResult]: ...
