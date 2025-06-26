# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from pydantic import BaseModel


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
