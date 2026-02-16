# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
from asyncio import CancelledError
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from typing import Annotated
from uuid import UUID

from kink import inject
from typing_extensions import Doc

from agentstack_server.api.schema.files import FileListQuery
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.file import (
    AsyncFile,
    Backend,
    ExtractedFileInfo,
    ExtractionMetadata,
    ExtractionStatus,
    File,
    FileType,
    TextExtraction,
    TextExtractionSettings,
)
from agentstack_server.domain.models.user import User
from agentstack_server.domain.repositories.file import IObjectStorageRepository, ITextExtractionBackend
from agentstack_server.exceptions import EntityNotFoundError, StorageCapacityExceededError
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class FileService:
    def __init__(
        self,
        object_storage_repository: IObjectStorageRepository,
        extraction_backend: ITextExtractionBackend,
        uow: IUnitOfWorkFactory,
        user_service: UserService,
        configuration: Configuration,
    ):
        self._object_storage = object_storage_repository
        self._uow = uow
        self._user_service = user_service
        self._storage_limit_per_user = configuration.object_storage.storage_limit_per_user_bytes
        self._storage_limit_per_file = configuration.object_storage.max_single_file_size
        self._extraction_backend = extraction_backend

    async def extract_text(self, file_id: UUID, job_id: str):
        """
        Extract text from a file using the configured extraction backend.

        This method coordinates the entire extraction process: fetching the file,
        extracting text, and uploading the extracted content.

        Args:
            file_id: ID of the file to extract text from
            job_id: Background job ID for tracking

        Raises:
            CancelledError: If the job is cancelled
            Exception: For any extraction or upload errors
        """
        error_log: list[str] = []
        extraction: TextExtraction | None = None
        file: File | None = None
        user: User | None = None
        uploaded_file_ids: list[UUID] = []

        try:
            async with self._uow() as uow:
                extraction = await uow.files.get_extraction_by_file_id(file_id=file_id)
                file = await uow.files.get(file_id=file_id)
                error_log.append(str(file.model_dump()))
                user = await uow.users.get(user_id=file.created_by)

                extraction.set_started(
                    job_id=job_id,
                    backend=self._extraction_backend.backend_name,
                )
                await uow.files.update_extraction(extraction=extraction)
                await uow.commit()

            file_url = await self._object_storage.get_file_url(file_id=file_id)
            error_log.append(f"file url: {file_url}")

            async with self._extraction_backend.extract_text(
                file_url=file_url,
                settings=extraction.extraction_metadata.settings if extraction.extraction_metadata else None,
            ) as extracted_files_iterator:
                extracted_files = []
                async for async_file, extraction_format in extracted_files_iterator:
                    extracted_db_file = await self.upload_file(
                        file=async_file,
                        user=user,
                        file_type=FileType.EXTRACTED_TEXT,
                        context_id=file.context_id,
                        parent_file_id=file_id,
                    )
                    uploaded_file_ids.append(extracted_db_file.id)
                    extracted_files.append(ExtractedFileInfo(file_id=extracted_db_file.id, format=extraction_format))

            extraction.set_completed(extracted_files=extracted_files)
            async with self._uow() as uow:
                await uow.files.update_extraction(extraction=extraction)
                await uow.commit()
            uploaded_file_ids.clear()
        except CancelledError:
            await self._cleanup_extracted_files(uploaded_file_ids)
            if extraction:
                async with self._uow() as uow:
                    extraction.set_cancelled()
                    await uow.files.update_extraction(extraction=extraction)
                    await uow.commit()
            raise
        except Exception as ex:
            error_log.append(str(ex))
            await self._cleanup_extracted_files(uploaded_file_ids)
            if extraction:
                async with self._uow() as uow:
                    extraction.set_failed("\n".join(str(e) for e in error_log))
                    await uow.files.update_extraction(extraction=extraction)
                    await uow.commit()
            raise

    async def upload_file(
        self,
        *,
        file: AsyncFile,
        user: User,
        file_type: FileType = FileType.USER_UPLOAD,
        context_id: UUID | None = None,
        parent_file_id: UUID | None = None,
    ) -> File:
        db_file = File(
            filename=file.filename,
            created_by=user.id,
            file_type=file_type,
            parent_file_id=parent_file_id,
            content_type=file.content_type,
            file_size_bytes=0,
            context_id=context_id,
        )
        try:
            async with self._uow() as uow:
                total_usage = await uow.files.total_usage(user_id=user.id)
                file = file.model_copy()
                max_size = min(self._storage_limit_per_user - total_usage, self._storage_limit_per_file)
                await uow.files.create(file=db_file)
                await uow.commit()

            file.read = limit_size_wrapper(read=file.read, max_size=max_size)
            db_file.file_size_bytes = await self._object_storage.upload_file(file_id=db_file.id, file=file)

            async with self._uow() as uow:
                await uow.files.update(file=db_file)
                await uow.commit()

            return db_file
        except Exception:
            # If the file was uploaded and then the commit failed, delete the file from the object storage.
            if db_file.file_size_bytes and db_file.file_size_bytes > 0:
                with suppress(Exception):
                    await self._object_storage.delete_files(file_ids=[db_file.id])

            with suppress(EntityNotFoundError):
                async with self._uow() as uow:
                    await uow.files.delete(file_id=db_file.id)
                    await uow.commit()

            raise

    async def get(self, *, file_id: UUID, user: User, context_id: UUID | None = None) -> File:
        async with self._uow() as uow:
            return await uow.files.get(file_id=file_id, user_id=user.id, context_id=context_id)

    @asynccontextmanager
    async def get_content(
        self, *, file_id: UUID, user: User, context_id: UUID | None = None
    ) -> AsyncIterator[AsyncFile]:
        async with self._uow() as uow:
            # check if the user owns the file
            await uow.files.get(file_id=file_id, user_id=user.id, context_id=context_id)

        async with self._object_storage.get_file(file_id=file_id) as file:
            yield file

    async def get_extraction(self, *, file_id: UUID, user: User, context_id: UUID | None = None) -> TextExtraction:
        async with self._uow() as uow:
            return await uow.files.get_extraction_by_file_id(file_id=file_id, user_id=user.id, context_id=context_id)

    async def delete(self, *, file_id: UUID, user: User, context_id: UUID | None = None) -> None:
        file_ids_to_delete = [file_id]
        deleted = False

        async with self._uow() as uow:
            # Find all extractions for this file and collect their extracted files
            try:
                extraction = await uow.files.get_extraction_by_file_id(
                    file_id=file_id, user_id=user.id, context_id=context_id
                )
                # Add all extracted file IDs to deletion list
                file_ids_to_delete.extend([ef.file_id for ef in extraction.extracted_files])
            except EntityNotFoundError:
                # No extraction exists for this file, which is fine
                pass

            # Delete from database first (this will cascade delete extractions and extraction_files)
            deleted = await uow.files.delete(file_id=file_id, user_id=user.id, context_id=context_id)
            await uow.commit()

        if deleted:
            await self._object_storage.delete_files(file_ids=file_ids_to_delete)

    async def _cleanup_extracted_files(self, file_ids: list[UUID]) -> None:
        """Best-effort cleanup for partially uploaded extracted files."""
        if not file_ids:
            return

        unique_ids = list(dict.fromkeys(file_ids))

        with suppress(Exception):
            await self._object_storage.delete_files(file_ids=unique_ids)

        with suppress(Exception):
            async with self._uow() as uow:
                for extracted_file_id in unique_ids:
                    await uow.files.delete(file_id=extracted_file_id)
                await uow.commit()

    async def create_extraction(
        self,
        *,
        file_id: UUID,
        user: User,
        context_id: UUID | None = None,
        settings: TextExtractionSettings,
    ) -> TextExtraction:
        async with self._uow() as uow:
            # Check user permissions
            await uow.files.get(file_id=file_id, user_id=user.id, context_id=context_id, file_type=FileType.USER_UPLOAD)
            try:
                # Check if extraction already exists
                extraction = await uow.files.get_extraction_by_file_id(file_id=file_id)
                match extraction.status:
                    case ExtractionStatus.COMPLETED | ExtractionStatus.PENDING | ExtractionStatus.IN_PROGRESS:
                        return extraction
                    case ExtractionStatus.FAILED | ExtractionStatus.CANCELLED:
                        extraction.reset_for_retry()
                        await uow.files.update_extraction(extraction=extraction)
                    case _:
                        raise TypeError(f"Unknown extraction status: {extraction.status}")
            except EntityNotFoundError:
                file_metadata = await self._object_storage.get_file_metadata(file_id=file_id)
                extraction = TextExtraction(file_id=file_id, extraction_metadata=ExtractionMetadata(settings=settings))

                # Docling doesn't support plain text nor markdown content-type, so we treat them as in-place extractions
                in_place_extraction = file_metadata.content_type in {"text/plain", "text/markdown"}
                if in_place_extraction:
                    extraction.set_completed(
                        extracted_files=[
                            ExtractedFileInfo(file_id=file_id, format=None)  # Point to itself since it's already text
                        ],
                        metadata=ExtractionMetadata(
                            backend=Backend.IN_PLACE, settings=None
                        ),  # Settings are ignored for in-place extraction
                    )
                await uow.files.create_extraction(extraction=extraction)
            if extraction.status == ExtractionStatus.PENDING:
                from agentstack_server.jobs.tasks.file import extract_text

                await extract_text.configure(queueing_lock=str(file_id)).defer_async(file_id=str(file_id))

            await uow.commit()
            return extraction

    async def delete_extraction(self, *, file_id: UUID, user: User, context_id: UUID | None = None) -> None:
        async with self._uow() as uow:
            extraction = await uow.files.get_extraction_by_file_id(
                file_id=file_id, user_id=user.id, context_id=context_id
            )

        file_ids_to_delete = [ef.file_id for ef in extraction.extracted_files if ef.file_id != file_id]
        if file_ids_to_delete:
            await self._object_storage.delete_files(file_ids=file_ids_to_delete)

        async with self._uow() as uow:
            for fid in file_ids_to_delete:
                await uow.files.delete(file_id=fid)

            await uow.files.delete_extraction(extraction_id=extraction.id)
            await uow.commit()

    async def list_files(
        self, query: FileListQuery, user: User, context_id: UUID | None = None
    ) -> PaginatedResult[File]:
        async with self._uow() as uow:
            return await uow.files.list_paginated(
                user_id=user.id,
                limit=query.limit,
                page_token=query.page_token,
                order=query.order,
                order_by=query.order_by,
                context_id=context_id,
                content_type=query.content_type,
                filename_search=query.filename_search,
            )


def limit_size_wrapper(
    read: Callable[[int], Awaitable[bytes]], max_size: int | None = None, size: int | None = None
) -> Callable[[int], Awaitable[bytes]]:
    current_size = 0

    # Quick check using the Content-Length header. This is not fully reliable as the header can be omitted or incorrect,
    # but it can reject large files early.
    if max_size is not None and size is not None and size > max_size:
        raise StorageCapacityExceededError("file", max_size)

    async def _read(size: Annotated[int, Doc("The number of bytes to read from the file.")] = -1) -> bytes:
        nonlocal current_size
        if max_size is None:
            return await read(size)

        chunk = await read(size)
        if chunk:
            current_size += len(chunk)
            if current_size > max_size:
                raise StorageCapacityExceededError("file", max_size)
        return chunk

    return _read
