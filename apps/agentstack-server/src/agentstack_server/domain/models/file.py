# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator, Awaitable, Callable
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field

from agentstack_server.utils.utils import utc_now


class FileType(StrEnum):
    USER_UPLOAD = "user_upload"
    EXTRACTED_TEXT = "extracted_text"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExtractionFormat(StrEnum):
    MARKDOWN = "markdown"
    VENDOR_SPECIFIC_JSON = "vendor_specific_json"


class TextExtractionSettings(BaseModel):
    formats: list[ExtractionFormat] = Field(
        default_factory=lambda: [ExtractionFormat.MARKDOWN, ExtractionFormat.VENDOR_SPECIFIC_JSON]
    )


class Backend(StrEnum):
    IN_PLACE = "in-place"


class ExtractionMetadata(BaseModel, extra="allow"):
    backend: str | None = None
    settings: TextExtractionSettings | None = None


class FileMetadata(BaseModel, extra="allow"):
    content_type: str
    filename: str
    content_length: int


class AsyncFile(BaseModel):
    filename: str
    content_type: str
    read: Callable[[int], Awaitable[bytes]]
    size: int | None = None

    @classmethod
    def from_async_iterator(cls, iterator: AsyncIterator[bytes], filename: str, content_type: str) -> Self:
        buffer = b""

        async def read(size: int = 8192) -> bytes:
            nonlocal buffer
            while len(buffer) < size:
                try:
                    buffer += await anext(iterator)
                except StopAsyncIteration:
                    break

            result = buffer[:size]
            buffer = buffer[size:]
            return result

        return cls(filename=filename, content_type=content_type, read=read)

    @classmethod
    def from_bytes(cls, content: bytes, filename: str, content_type: str) -> Self:
        pos = 0

        async def read(size: int = 8192) -> bytes:
            nonlocal pos
            result = content[pos : pos + size]
            pos += len(result)
            return result

        return cls(filename=filename, content_type=content_type, read=read, size=len(content))


class File(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    content_type: str = Field(max_length=256)
    file_size_bytes: int | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    file_type: FileType = FileType.USER_UPLOAD
    parent_file_id: UUID | None = None
    context_id: UUID | None = None


class ExtractedFileInfo(BaseModel):
    """Information about an extracted file."""

    file_id: UUID
    format: ExtractionFormat | None = None


class TextExtraction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    file_id: UUID
    extracted_files: list[ExtractedFileInfo] = Field(default_factory=list)
    status: ExtractionStatus = ExtractionStatus.PENDING
    job_id: str | None = None
    error_message: str | None = None
    extraction_metadata: ExtractionMetadata | None = None
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)

    def set_started(self, job_id: str, backend: str) -> None:
        """Mark extraction as started with job ID and backend name."""
        self.status = ExtractionStatus.IN_PROGRESS
        self.job_id = job_id
        self.started_at = utc_now()
        self.error_message = None

        # Create extraction_metadata if it doesn't exist
        if self.extraction_metadata is None:
            self.extraction_metadata = ExtractionMetadata()

        # Set the backend name
        self.extraction_metadata.backend = backend

    def set_completed(
        self, extracted_files: list[ExtractedFileInfo], metadata: ExtractionMetadata | None = None
    ) -> None:
        """Mark extraction as completed with extracted files and their formats."""
        self.status = ExtractionStatus.COMPLETED
        self.extracted_files = extracted_files
        self.finished_at = utc_now()
        self.error_message = None
        if metadata is not None:
            self.extraction_metadata = metadata

    def set_failed(self, error_message: str) -> None:
        """Mark extraction as failed with error message."""
        self.status = ExtractionStatus.FAILED
        self.error_message = error_message
        self.finished_at = utc_now()

    def set_cancelled(self) -> None:
        """Mark extraction as cancelled."""
        self.status = ExtractionStatus.CANCELLED
        self.finished_at = utc_now()

    def reset_for_retry(self) -> None:
        """Reset extraction for retry (clears error state)."""
        self.status = ExtractionStatus.PENDING
        self.error_message = None
        self.started_at = None
        self.finished_at = None
        self.job_id = None

    def find_file_by_format(self, format: ExtractionFormat | None) -> UUID | None:
        """Find an extracted file by format from the extracted files list."""
        for extracted_file_info in self.extracted_files:
            if extracted_file_info.format == format:
                return extracted_file_info.file_id
        return None
