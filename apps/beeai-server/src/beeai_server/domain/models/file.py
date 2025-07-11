# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Awaitable, Callable
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field

from beeai_server.utils.utils import utc_now


class FileType(StrEnum):
    user_upload = "user_upload"
    extracted_text = "extracted_text"


class ExtractionStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ExtractionMetadata(BaseModel, extra="allow"):
    backend: str


class FileMetadata(BaseModel, extra="allow"):
    content_type: str
    filename: str
    content_length: int


class AsyncFile(BaseModel):
    filename: str
    content_type: str
    read: Callable[[int], Awaitable[bytes]]
    size: int | None = None


class File(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    file_size_bytes: int | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    file_type: FileType = FileType.user_upload
    parent_file_id: UUID | None = None


class TextExtraction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    file_id: UUID
    extracted_file_id: UUID | None = None
    status: ExtractionStatus = ExtractionStatus.pending
    job_id: str | None = None
    error_message: str | None = None
    extraction_metadata: ExtractionMetadata | None = None
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)

    def set_started(self, job_id: str) -> None:
        """Mark extraction as started with job ID."""
        self.status = ExtractionStatus.in_progress
        self.job_id = job_id
        self.started_at = utc_now()
        self.error_message = None

    def set_completed(self, extracted_file_id: UUID, metadata: ExtractionMetadata | None = None) -> None:
        """Mark extraction as completed with extracted file ID."""
        self.status = ExtractionStatus.completed
        self.extracted_file_id = extracted_file_id
        self.finished_at = utc_now()
        self.extraction_metadata = metadata
        self.error_message = None

    def set_failed(self, error_message: str) -> None:
        """Mark extraction as failed with error message."""
        self.status = ExtractionStatus.failed
        self.error_message = error_message
        self.finished_at = utc_now()

    def set_cancelled(self) -> None:
        """Mark extraction as cancelled."""
        self.status = ExtractionStatus.cancelled
        self.finished_at = utc_now()

    def reset_for_retry(self) -> None:
        """Reset extraction for retry (clears error state)."""
        self.status = ExtractionStatus.pending
        self.error_message = None
        self.started_at = None
        self.finished_at = None
        self.job_id = None
