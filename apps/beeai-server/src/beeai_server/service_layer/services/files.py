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
from contextlib import suppress, asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.domain.models.file import AsyncFile, File
from beeai_server.domain.models.user import User
from beeai_server.domain.repositories.files import IObjectStorageRepository
from beeai_server.service_layer.services.users import UserService
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.fastapi import limit_size_wrapper

logger = logging.getLogger(__name__)


@inject
class FileService:
    def __init__(
        self,
        object_storage_repository: IObjectStorageRepository,
        uow: IUnitOfWorkFactory,
        user_service: UserService,
        configuration: Configuration,
    ):
        self._object_storage = object_storage_repository
        self._uow = uow
        self._user_service = user_service
        self._storage_limit_per_user = configuration.object_storage.storage_limit_per_user_bytes
        self._storage_limit_per_file = configuration.object_storage.max_single_file_size

    async def upload_file(self, *, file: AsyncFile, user: User) -> File:
        db_file = File(filename=file.filename, created_by=user.id)
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
                    await self._object_storage.delete_file(file_id=db_file.id)
            raise

    async def get(self, *, file_id: UUID, user: User) -> File:
        async with self._uow() as uow:
            return await uow.files.get(file_id=file_id, user_id=user.id)

    @asynccontextmanager
    async def get_content(self, *, file_id: UUID, user: User) -> AsyncIterator[AsyncFile]:
        async with self._uow() as uow:
            await uow.files.get(file_id=file_id, user_id=user.id)  # check if the user owns the file
            async with self._object_storage.get_file(file_id=file_id) as file:
                yield file

    async def delete(self, *, file_id: UUID, user: User) -> None:
        async with self._uow() as uow:
            await uow.files.delete(file_id=file_id, user_id=user.id)
            await self._object_storage.delete_file(file_id=file_id)
            await uow.commit()
