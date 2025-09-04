# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field

from beeai_server.domain.models.common import Metadata
from beeai_server.utils.utils import utc_now


class VectorStoreStats(BaseModel):
    usage_bytes: int
    num_documents: int


class VectorStore(BaseModel):
    """A vector store containing embeddings for text content."""

    id: UUID = Field(default_factory=uuid4)
    name: str | None = None
    model_id: str
    dimension: int = Field(gt=0, lt=10_000)
    created_at: AwareDatetime = Field(default_factory=utc_now)
    last_active_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    stats: VectorStoreStats | None = None
    context_id: UUID | None = None


class VectorStoreDocument(BaseModel):
    id: str
    vector_store_id: UUID
    file_id: UUID | None = None
    usage_bytes: int | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)


class VectorSearchResult(BaseModel):
    """Result of a vector search operation."""

    text: str
    score: float
    metadata: dict | None = None


class DocumentType(StrEnum):
    PLATFORM_FILE = "platform_file"
    EXTERNAL = "external"


class VectorStoreDocumentInfo(BaseModel):
    id: str
    usage_bytes: int = None


class VectorStoreItem(BaseModel):
    """A single item in a vector store, containing text content and its vector embedding."""

    id: UUID = Field(default_factory=uuid4)
    document_id: str
    document_type: DocumentType = DocumentType.PLATFORM_FILE
    model_id: str | Literal["platform"] = "platform"
    text: str
    embedding: list[float]
    metadata: Metadata | None = None


class VectorStoreSearchResult(BaseModel):
    """Result of a vector store search operation containing full item data and similarity score."""

    item: VectorStoreItem
    score: float
