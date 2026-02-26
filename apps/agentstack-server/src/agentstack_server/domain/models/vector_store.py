# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from agentstack_server.domain.models.common import Metadata
from agentstack_server.utils.utils import utc_now


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
    usage_bytes: int | None = None


class VectorStoreItem(BaseModel):
    """A single item in a vector store, containing text content and its vector embedding."""

    id: UUID = Field(default_factory=uuid4)
    document_id: str
    document_type: DocumentType = DocumentType.PLATFORM_FILE
    model_id: str | Literal["platform"] = "platform"
    text: str
    embedding: list[float]
    metadata: Metadata | None = None

    @model_validator(mode="after")
    def validate_document_id(self) -> Self:
        """Validate that document_id is a valid UUID when document_type is platform_file."""
        if self.document_type == DocumentType.PLATFORM_FILE:
            try:
                _ = UUID(self.document_id)
            except ValueError as ex:
                raise ValueError(
                    f"document_id must be a valid UUID when document_type is platform_file, got: {self.document_id}"
                ) from ex
        return self


class VectorStoreSearchResult(BaseModel):
    """Result of a vector store search operation containing full item data and similarity score."""

    item: VectorStoreItem
    score: float
