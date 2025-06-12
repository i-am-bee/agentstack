# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from beeai_server.domain.models.file import AsyncFile, File

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, file_service: FileServiceDependency, user: AuthenticatedUserDependency) -> File:
    return await file_service.upload_file(
        file=AsyncFile(filename=file.filename, content_type=file.content_type, read=file.read, size=file.size),
        user=user,
    )


@router.get("/{file_id}")
async def get_file(file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency) -> File:
    return await file_service.get(file_id=file_id, user=user)


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: UUID, file_service: FileServiceDependency, user: AuthenticatedUserDependency
) -> StreamingResponse:
    exit_stack = AsyncExitStack()
    file = await exit_stack.enter_async_context(file_service.get_content(file_id=file_id, user=user))

    async def iter_file(chunk_size=8192):
        try:
            while chunk := await file.read(chunk_size):
                yield chunk
        finally:
            await exit_stack.aclose()

    return StreamingResponse(content=iter_file(), media_type=file.content_type)


@router.delete("/{file_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    file_service: FileServiceDependency,
    user: AuthenticatedUserDependency,
) -> None:
    await file_service.delete(file_id=file_id, user=user)
