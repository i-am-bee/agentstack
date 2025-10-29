# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import timedelta
from uuid import UUID

from a2a.types import Artifact, Message, Role, TextPart
from fastapi import status
from kink import di, inject
from pydantic import TypeAdapter

from agentstack_server.api.schema.common import PaginationQuery
from agentstack_server.api.schema.openai import ChatCompletionRequest
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.common import Metadata, MetadataPatch, PaginatedResult
from agentstack_server.domain.models.context import (
    Context,
    ContextHistoryItem,
    ContextHistoryItemData,
    TitleGenerationState,
)
from agentstack_server.domain.models.user import User
from agentstack_server.domain.repositories.file import IObjectStorageRepository
from agentstack_server.exceptions import PlatformError
from agentstack_server.service_layer.services.model_providers import ModelProviderService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.utils import filter_dict, utc_now

logger = logging.getLogger(__name__)


@inject
class ContextService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration, object_storage: IObjectStorageRepository):
        self._uow = uow
        self._object_storage = object_storage
        self._configuration = configuration
        self._expire_resources_after = timedelta(days=configuration.context.resource_expire_after_days)

    async def create(self, *, user: User, metadata: Metadata, provider_id: UUID | None = None) -> Context:
        context = Context(created_by=user.id, metadata=metadata, provider_id=provider_id)
        async with self._uow() as uow:
            await uow.contexts.create(context=context)
            await uow.commit()
            return context

    async def get(self, *, context_id: UUID, user: User) -> Context:
        async with self._uow() as uow:
            return await uow.contexts.get(context_id=context_id, user_id=user.id)

    async def list(
        self, *, user: User, pagination: PaginationQuery, include_empty: bool = True, provider_id: UUID | None = None
    ) -> PaginatedResult[Context]:
        async with self._uow() as uow:
            return await uow.contexts.list_paginated(
                user_id=user.id,
                provider_id=provider_id,
                limit=pagination.limit,
                page_token=pagination.page_token,
                order=pagination.order,
                order_by=pagination.order_by,
                include_empty=include_empty,
            )

    async def update(self, *, context_id: UUID, metadata: Metadata | None, user: User) -> Context:
        async with self._uow() as uow:
            context = await uow.contexts.get(context_id=context_id, user_id=user.id)
            context.metadata = metadata
            context.updated_at = utc_now()
            await uow.contexts.update(context=context)
            await uow.commit()
        return context

    async def patch_metadata(self, *, context_id: UUID, metadata_patch: MetadataPatch, user: User) -> Context:
        async with self._uow() as uow:
            context = await uow.contexts.get(context_id=context_id, user_id=user.id)
            deleted_keys = {k for k, v in metadata_patch.items() if v is None}
            try:
                context.metadata = TypeAdapter(Metadata).validate_python(
                    {
                        **{k: v for k, v in (context.metadata or {}).items() if k not in deleted_keys},
                        **filter_dict(metadata_patch),
                    }
                )
            except ValueError as e:  # maximum number of keys exceeded
                raise PlatformError(str(e), status_code=status.HTTP_400_BAD_REQUEST) from e
            context.updated_at = utc_now()
            await uow.contexts.update(context=context)
            await uow.commit()
        return context

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
            async for context in uow.contexts.list(last_active_before=utc_now() - self._expire_resources_after):
                deleted_stats.update(await self._cleanup_expired_resources(context_id=context.id))
        return deleted_stats

    async def update_last_active(self, *, context_id: UUID) -> None:
        async with self._uow() as uow:
            await uow.contexts.update_last_active(context_id=context_id)
            await uow.commit()

    def _extract_text(self, msg: Message | Artifact) -> str | None:
        for part in msg.parts:
            if isinstance(part.root, TextPart):
                return part.root.text
        return None

    async def add_history_item(self, *, context_id: UUID, data: ContextHistoryItemData, user: User) -> None:
        async with self._uow() as uow:
            context = await uow.contexts.get(context_id=context_id, user_id=user.id)
            await uow.contexts.add_history_item(
                context_id=context_id,
                history_item=ContextHistoryItem(context_id=context_id, data=data),
            )

            if getattr(data, "role", None) == Role.user and not (context.metadata or {}).get("title"):
                from agentstack_server.jobs.tasks.context import generate_conversation_title as task

                title = self._extract_text(data) or "Untitled"
                title = f"{title[:100]}..." if len(title) > 100 else title

                should_generate_title = self._configuration.features.generate_conversation_title
                state = TitleGenerationState.PENDING if should_generate_title else TitleGenerationState.COMPLETED
                await uow.contexts.update_title(context_id=context_id, title=title, generation_state=state)

                if should_generate_title:
                    await task.configure(queueing_lock=str(context_id)).defer_async(context_id=str(context_id))

            await uow.commit()

    async def generate_conversation_title(self, *, context_id: UUID):
        from agentstack_server.api.routes.openai import create_chat_completion

        async with self._uow() as uow:
            msg = await uow.contexts.list_history(context_id=context_id, limit=1, order="desc", order_by="created_at")
            config = await uow.configuration.get_system_configuration()

        if not msg.items:
            logger.warning(f"Cannot generate title for context {context_id}: no history found.")
            return
        if not (text := self._extract_text(msg.items[0].data)):
            logger.warning(f"Cannot generate title for context {context_id}: first message has no text.")
            return
        if not config.default_llm_model:
            logger.warning(f"Cannot generate title for context {context_id}: default LLM model not set.")
            return

        try:
            # HACK: calling the endpoint directly (instead, logic should be extracted from the api layer to domain)
            resp = await create_chat_completion(
                model_provider_service=di[ModelProviderService],
                request=ChatCompletionRequest(
                    model=config.default_llm_model,
                    stream=False,
                    max_completion_tokens=100,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Write a short descriptive title for the conversation (max 100 characters). "
                                "Return only the title verbatim with no commentary or explanation"
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                ),
                _=None,  # pyright: ignore [reportArgumentType]
            )
            title = resp["choices"][0]["message"]["content"]  # pyright: ignore [reportIndexIssue]
            title = f"{title[:100]}..." if len(title) > 100 else title
            async with self._uow() as uow:
                await uow.contexts.update_title(
                    context_id=context_id, title=title, generation_state=TitleGenerationState.COMPLETED
                )
                await uow.commit()
        except Exception as e:
            async with self._uow() as uow:
                await uow.contexts.update_title(
                    context_id=context_id, title=None, generation_state=TitleGenerationState.FAILED
                )
                await uow.commit()
            logger.warning(f"Failed to generate title for context {context_id}: {e}")
            raise e

    async def list_history(
        self, *, context_id: UUID, user: User, pagination: PaginationQuery
    ) -> PaginatedResult[ContextHistoryItem]:
        async with self._uow() as uow:
            await uow.contexts.get(context_id=context_id, user_id=user.id)
            return await uow.contexts.list_history(
                context_id=context_id,
                limit=pagination.limit,
                page_token=pagination.page_token,
                order=pagination.order,
                order_by=pagination.order_by,
            )
