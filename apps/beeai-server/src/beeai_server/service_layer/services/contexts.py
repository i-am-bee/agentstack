# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import UUID

from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.domain.models.context import Context
from beeai_server.domain.models.user import User
from beeai_server.domain.repositories.file import IObjectStorageRepository
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


@inject
class ContextService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration, object_storage: IObjectStorageRepository):
        self._uow = uow
        self._object_storage = object_storage
        self._configuration = configuration
        self._expire_resources_after = timedelta(days=configuration.context.resource_expire_after_days)

    async def create(self, *, user: User) -> Context:
        context = Context(created_by=user.id)
        async with self._uow() as uow:
            await uow.contexts.create(context=context)
            await uow.commit()
            return context

    async def get(self, *, context_id: UUID, user: User) -> Context:
        async with self._uow() as uow:
            return await uow.contexts.get(context_id=context_id, user_id=user.id)

    async def list(self, *, user: User) -> AsyncIterator[Context]:
        async with self._uow() as uow:
            async for context in uow.contexts.list(user_id=user.id):
                yield context

    async def delete(self, *, context_id: UUID, user: User) -> None:
        """Delete context and all attached resources"""
        async with self._uow() as uow:
            await uow.contexts.get(context_id=context_id, user_id=user.id)

            # Files
            file_ids = [file.id async for file in uow.files.list(user_id=user.id, context_id=context_id)]
            await self._object_storage.delete_files(file_ids=file_ids)
            # File DB objects are deleted automatically using cascade

            # Vector stores
            # deleted automatically using cascade

            await uow.contexts.delete(context_id=context_id, user_id=user.id)
            await uow.commit()

    async def _cleanup_expired_resources(self, context_id: UUID) -> dict[str, int]:
        """Delete resources attached to context"""
        deleted_stats = {"files": 0, "vector_stores": 0}
        async with self._uow() as uow:
            # Files
            file_ids = [file.id async for file in uow.files.list(context_id=context_id)]
            await self._object_storage.delete_files(file_ids=file_ids)
            deleted_stats["files"] = await uow.files.delete(context_id=context_id)

            # Vector stores
            deleted_stats["vector_stores"] = await uow.vector_stores.delete(context_id=context_id)
            await uow.commit()
        return deleted_stats

    async def expire_resources(self) -> dict[str, int]:
        deleted_stats = {}
        async with self._uow() as uow:
            async for context in uow.contexts.list():
                if utc_now() - context.last_active_at > self._expire_resources_after:
                    deleted_stats.update(await self._cleanup_expired_resources(context_id=context.id))
        return deleted_stats

    async def update_last_active(self, *, context_id: UUID) -> None:
        async with self._uow() as uow:
            await uow.contexts.update_last_active(context_id=context_id)
            await uow.commit()
