# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import AsyncExitStack
from uuid import UUID

import fastapi
from fastapi import APIRouter, UploadFile, status
from fastapi.responses import StreamingResponse

from beeai_server.api.dependencies import (
    FileServiceDependency,
    AuthenticatedUserDependency,
)
from beeai_server.api.schema.common import EntityModel
from beeai_server.domain.models.file import AsyncFile, File, TextExtraction
from beeai_server.domain.models.user import User
from beeai_server.service_layer.services.files import FileService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> EntityModel[File]:
    return await file_service.upload_file(
        file=AsyncFile(filename=file.filename, content_type=file.content_type, read=file.read, size=file.size),
        user=user,
    )


@router.get("/{file_id}")
async def get_file(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> EntityModel[File]:
    return await file_service.get(file_id=file_id, user=user)


async def _stream_file(*, file_service: FileService, user: User, file_id: UUID) -> StreamingResponse:
    exit_stack = AsyncExitStack()
    file = await exit_stack.enter_async_context(file_service.get_content(file_id=file_id, user=user))

    async def iter_file(chunk_size=8192):
        try:
            while chunk := await file.read(chunk_size):
                yield chunk
        finally:
            await exit_stack.aclose()

    return StreamingResponse(content=iter_file(), media_type=file.content_type)


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> StreamingResponse:
    return await _stream_file(file_service=file_service, user=user, file_id=file_id)


@router.get("/{file_id}/text_content")
async def get_text_file_content(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> StreamingResponse:
    extraction = await file_service.get_extraction(file_id=file_id, user=user)
    return await _stream_file(file_service=file_service, user=user, file_id=extraction.extracted_file_id)


@router.delete("/{file_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency) -> None:
    await file_service.delete(file_id=file_id, user=user)


@router.post("/{file_id}/extraction", status_code=status.HTTP_201_CREATED)
async def create_text_extraction(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> EntityModel[TextExtraction]:
    """Create or return text extraction for a file.

    - If extraction is completed, returns existing result
    - If extraction failed, retries the extraction
    - If extraction is pending/in-progress, returns current status
    - If no extraction exists, creates a new one
    """
    return await file_service.create_extraction(file_id=file_id, user=user)


@router.get("/{file_id}/extraction")
async def get_text_extraction(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> EntityModel[TextExtraction]:
    return await file_service.get_extraction(file_id=file_id, user=user)


@router.delete("/{file_id}/extraction", status_code=status.HTTP_204_NO_CONTENT)
async def delete_text_extraction(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> None:
    await file_service.delete_extraction(file_id=file_id, user=user)
