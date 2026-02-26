# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from agentstack_server.api.schema.common import PaginationQuery
from agentstack_server.domain.models.file import TextExtractionSettings


class FileResponse(BaseModel):
    """Response schema for file operations."""

    file_id: UUID
    url: str | None = None


class FileUploadResponse(FileResponse):
    """Response schema for file upload."""

    pass


class FileUrlResponse(BaseModel):
    """Response schema for file URL."""

    url: str


class FileListQuery(PaginationQuery):
    """Query schema for listing files."""

    content_type: str | None = None
    filename_search: str | None = Field(
        default=None,
        description="Case-insensitive partial match search on filename (e.g., 'doc' matches 'my_document.pdf')",
    )
    order_by: str = Field(default_factory=lambda: "created_at", pattern="^created_at|filename|file_size_bytes$")


class TextExtractionRequest(BaseModel):
    """Request schema for text extraction."""

    settings: TextExtractionSettings | None = Field(
        default=None,
        description="Additional options for text extraction",
    )
