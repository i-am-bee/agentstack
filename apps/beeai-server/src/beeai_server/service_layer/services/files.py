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

from beeai_server.configuration import Configuration
from beeai_server.domain.models.file import (
    AsyncFile,
    ExtractionMetadata,
    ExtractionStatus,
    File,
    FileType,
    TextExtraction,
)
from beeai_server.domain.models.user import User
from beeai_server.domain.repositories.file import IObjectStorageRepository, ITextExtractionBackend
from beeai_server.exceptions import EntityNotFoundError, StorageCapacityExceededError
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

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
        error_log = []
        async with self._uow() as uow:
            extraction = await uow.files.get_extraction_by_file_id(file_id=file_id)
            file = await uow.files.get(file_id=file_id)
            error_log.append(file.model_dump())
            user = await uow.users.get(user_id=file.created_by)
            extraction.set_started(job_id=job_id)
            await uow.files.update_extraction(extraction=extraction)
            await uow.commit()
        try:
            file_url = await self._object_storage.get_file_url(file_id=file_id)
            error_log.append(f"file url: {file_url}")
            async with self._extraction_backend.extract_text(file_url=file_url) as extracted_file:
                extracted_db_file = await self.upload_file(
                    file=extracted_file,
                    user=user,
                    file_type=FileType.extracted_text,
                    context_id=file.context_id,
                    parent_file_id=file_id,
                )
            extraction.set_completed(extracted_file_id=extracted_db_file.id)
            async with self._uow() as uow:
                await uow.files.update_extraction(extraction=extraction)
                await uow.commit()
        except CancelledError:
            async with self._uow() as uow:
                extraction.set_cancelled()
                await uow.files.update_extraction(extraction=extraction)
                await uow.commit()
            raise
        except Exception as ex:
            error_log.append(str(ex))
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
        file_type: FileType = FileType.user_upload,
        context_id: UUID | None = None,
        parent_file_id: UUID | None = None,
    ) -> File:
        db_file = File(
            filename=file.filename,
            created_by=user.id,
            file_type=file_type,
            parent_file_id=parent_file_id,
            content_type=file.content_type,
            context_id=context_id,
        )
        try:
            async with self._uow() as uow:
                total_usage = await uow.files.total_usage(user_id=user.id)
                file = file.model_copy()
                max_size = min(self._storage_limit_per_user - total_usage, self._storage_limit_per_file)
                file.read = limit_size_wrapper(read=file.read, max_size=max_size)

                db_file.file_size_bytes = await self._object_storage.upload_file(file_id=db_file.id, file=file)
                await uow.files.create(file=db_file)
                await uow.commit()
                return db_file
        except Exception:
            # If the file was uploaded and then the commit failed, delete the file from the object storage.
            if db_file.file_size_bytes is not None:
                with suppress(Exception):
                    await self._object_storage.delete_files(file_ids=[db_file.id])
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
        async with self._uow() as uow:
            if await uow.files.delete(file_id=file_id, user_id=user.id, context_id=context_id):
                await self._object_storage.delete_files(file_ids=[file_id])
                await uow.commit()

    async def create_extraction(self, *, file_id: UUID, user: User, context_id: UUID | None = None) -> TextExtraction:
        async with self._uow() as uow:
            # Check user permissions
            await uow.files.get(file_id=file_id, user_id=user.id, context_id=context_id, file_type=FileType.user_upload)
            try:
                # Check if extraction already exists
                extraction = await uow.files.get_extraction_by_file_id(file_id=file_id)
                match extraction.status:
                    case ExtractionStatus.completed | ExtractionStatus.pending | ExtractionStatus.in_progress:
                        return extraction
                    case ExtractionStatus.failed | ExtractionStatus.cancelled:
                        extraction.reset_for_retry()
                        await uow.files.update_extraction(extraction=extraction)
                    case _:
                        raise TypeError(f"Unknown extraction status: {extraction.status}")
            except EntityNotFoundError:
                file_metadata = await self._object_storage.get_file_metadata(file_id=file_id)
                extraction = TextExtraction(file_id=file_id)
                if file_metadata.content_type in {"text/plain", "text/markdown"}:
                    extraction.set_completed(
                        extracted_file_id=file_id,  # Point to itself since it's already text
                        metadata=ExtractionMetadata(backend="in-place"),
                    )
                await uow.files.create_extraction(extraction=extraction)
            if extraction.status == ExtractionStatus.pending:
                from beeai_server.jobs.tasks.file import extract_text

                await extract_text.configure(queueing_lock=str(file_id)).defer_async(file_id=str(file_id))

            await uow.commit()
            return extraction

    async def delete_extraction(self, *, file_id: UUID, user: User, context_id: UUID | None = None) -> None:
        async with self._uow() as uow:
            extraction = await uow.files.get_extraction_by_file_id(
                file_id=file_id, user_id=user.id, context_id=context_id
            )

            if extraction.extracted_file_id and extraction.extracted_file_id != file_id:
                await self._object_storage.delete_files(file_ids=[extraction.extracted_file_id])
                await uow.files.delete(file_id=extraction.extracted_file_id)

            await uow.files.delete_extraction(extraction_id=extraction.id)
            await uow.commit()


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

        if chunk := await read(size):
            current_size += len(chunk)
            if current_size > max_size:
                raise StorageCapacityExceededError("file", max_size)
        return chunk

    return _read
