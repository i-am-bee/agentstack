# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import AsyncExitStack
from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from beeai_server.api.dependencies import (
    FileServiceDependency,
    RequiresContextPermissions,
)
from beeai_server.api.schema.common import EntityModel
from beeai_server.domain.models.file import AsyncFile, ExtractionStatus, File, TextExtraction
from beeai_server.domain.models.permissions import AuthorizedUser
from beeai_server.service_layer.services.files import FileService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"write"}))],
) -> EntityModel[File]:
    if not file.filename or not file.content_type:
        raise fastapi.HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename or content type")
    return EntityModel(
        await file_service.upload_file(
            file=AsyncFile(filename=file.filename, content_type=file.content_type, read=file.read, size=file.size),
            user=user.user,
            context_id=user.context_id,
        )
    )


@router.get("/{file_id}")
async def get_file(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"read"}))],
) -> EntityModel[File]:
    return EntityModel(await file_service.get(file_id=file_id, user=user.user, context_id=user.context_id))


async def _stream_file(*, file_service: FileService, user: AuthorizedUser, file_id: UUID) -> StreamingResponse:
    exit_stack = AsyncExitStack()
    file = await exit_stack.enter_async_context(
        file_service.get_content(file_id=file_id, user=user.user, context_id=user.context_id)
    )

    async def iter_file(chunk_size=8192):
        try:
            while chunk := await file.read(chunk_size):
                yield chunk
        finally:
            await exit_stack.aclose()

    return StreamingResponse(content=iter_file(), media_type=file.content_type)


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"read"}))],
) -> StreamingResponse:
    return await _stream_file(file_service=file_service, user=user, file_id=file_id)


@router.get("/{file_id}/text_content")
async def get_text_file_content(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"read"}))],
) -> StreamingResponse:
    extraction = await file_service.get_extraction(file_id=file_id, user=user.user, context_id=user.context_id)
    if not extraction.status == ExtractionStatus.COMPLETED or not extraction.extracted_file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extraction is not completed (status {extraction.status})",
        )
    return await _stream_file(file_service=file_service, user=user, file_id=extraction.extracted_file_id)


@router.delete("/{file_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"write"}))],
) -> None:
    await file_service.delete(file_id=file_id, user=user.user, context_id=user.context_id)


@router.post("/{file_id}/extraction", status_code=status.HTTP_201_CREATED)
async def create_text_extraction(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"write", "extract"}))],
) -> EntityModel[TextExtraction]:
    """Create or return text extraction for a file.

    - If extraction is completed, returns existing result
    - If extraction failed, retries the extraction
    - If extraction is pending/in-progress, returns current status
    - If no extraction exists, creates a new one
    """
    return EntityModel(
        await file_service.create_extraction(file_id=file_id, user=user.user, context_id=user.context_id)
    )


@router.get("/{file_id}/extraction")
async def get_text_extraction(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"read"}))],
) -> EntityModel[TextExtraction]:
    return EntityModel(await file_service.get_extraction(file_id=file_id, user=user.user, context_id=user.context_id))


@router.delete("/{file_id}/extraction", status_code=status.HTTP_204_NO_CONTENT)
async def delete_text_extraction(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissions(files={"write"}))],
) -> None:
    await file_service.delete_extraction(file_id=file_id, user=user.user, context_id=user.context_id)
