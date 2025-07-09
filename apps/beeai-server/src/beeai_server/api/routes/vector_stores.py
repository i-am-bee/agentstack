# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import UUID

from fastapi import APIRouter, status

from beeai_server.api.dependencies import AuthenticatedUserDependency, VectorStoreServiceDependency
from beeai_server.api.schema.common import EntityModel, PaginatedResponse
from beeai_server.api.schema.vector_stores import (
    CreateVectorStoreRequest,
    SearchRequest,
)
from beeai_server.domain.models.vector_store import (
    VectorStore,
    VectorStoreDocument,
    VectorStoreItem,
    VectorStoreSearchResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_vector_store(
    request: CreateVectorStoreRequest,
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> EntityModel[VectorStore]:
    """Create a new vector store."""
    return await vector_store_service.create(
        name=request.name, dimension=request.dimension, user=user, model_id=request.model_id
    )


@router.get("/{vector_store_id}")
async def get_vector_store(
    vector_store_id: UUID,
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> EntityModel[VectorStore]:
    """Get a vector store by ID."""
    return await vector_store_service.get(vector_store_id=vector_store_id, user=user)


@router.delete("/{vector_store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vector_store(
    vector_store_id: UUID,
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> None:
    """Delete a vector store by ID."""
    await vector_store_service.delete(vector_store_id=vector_store_id, user=user)


@router.put("/{vector_store_id}")
async def add_items(
    vector_store_id: UUID,
    items: list[VectorStoreItem],
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> None:
    await vector_store_service.add_items(vector_store_id=vector_store_id, items=items, user=user)


@router.post("/{vector_store_id}/search")
async def search_with_vector(
    vector_store_id: UUID,
    request: SearchRequest,
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> PaginatedResponse[VectorStoreSearchResult]:
    """Search a vector store using either text or a vector."""
    response = await vector_store_service.search(
        vector_store_id=vector_store_id,
        query_vector=request.query_vector,
        limit=request.limit,
        user=user,
    )
    return PaginatedResponse(items=response, total_count=len(response))


@router.get("/{vector_store_id}/documents")
async def list_documents(
    vector_store_id: UUID,
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> PaginatedResponse[VectorStoreDocument]:
    """List all documents in a vector store."""
    documents = await vector_store_service.list_documents(vector_store_id=vector_store_id, user=user)
    return PaginatedResponse(items=documents, total_count=len(documents))


@router.delete("/{vector_store_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    vector_store_id: UUID,
    document_id: str,
    vector_store_service: VectorStoreServiceDependency,
    user: AuthenticatedUserDependency,
) -> None:
    """Delete a document by ID."""
    await vector_store_service.remove_documents(vector_store_id=vector_store_id, document_ids=[document_id], user=user)
