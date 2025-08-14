# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import AnyUrl, HttpUrl

from beeai_server.domain.models.file import AsyncFile, File, FileMetadata, FileType, TextExtraction


class IFileRepository(Protocol):
    async def list(self, *, user_id: UUID | None = None, context_id: UUID | None = None) -> AsyncIterator[File]:
        yield  # type: ignore

    async def create(self, *, file: File) -> None: ...
    async def total_usage(self, *, user_id: UUID | None = None) -> int: ...
    async def get(
        self,
        *,
        file_id: UUID,
        user_id: UUID | None = None,
        context_id: UUID | None = None,
        file_type: FileType | None = None,
    ) -> File: ...
    async def delete(
        self, *, file_id: UUID | None = None, user_id: UUID | None = None, context_id: UUID | None = None
    ) -> int: ...

    # Text extraction methods
    async def create_extraction(self, *, extraction: TextExtraction) -> None: ...
    async def get_extraction_by_file_id(
        self, *, file_id: UUID, user_id: UUID | None = None, context_id: UUID | None = None
    ) -> TextExtraction: ...
    async def update_extraction(self, *, extraction: TextExtraction) -> None: ...
    async def delete_extraction(self, *, extraction_id: UUID) -> int: ...


@runtime_checkable
class IObjectStorageRepository(Protocol):
    async def upload_file(self, *, file_id: UUID, file: AsyncFile) -> int: ...

    @asynccontextmanager
    async def get_file(self, *, file_id: UUID) -> AsyncIterator[AsyncFile]:
        yield  # type: ignore

    async def delete_files(self, *, file_ids: list[UUID]) -> None: ...
    async def get_file_url(self, *, file_id: UUID) -> HttpUrl: ...
    async def get_file_metadata(self, *, file_id: UUID) -> FileMetadata: ...


@runtime_checkable
class ITextExtractionBackend(Protocol):
    @asynccontextmanager
    async def extract_text(self, *, file_url: AnyUrl, timeout: timedelta | None = None) -> AsyncIterator[AsyncFile]:  # noqa: ASYNC109
        yield ...  # pyright: ignore [reportReturnType]
