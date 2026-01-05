# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections.abc import Sequence
from contextlib import suppress
from datetime import timedelta
from uuid import UUID

from a2a.types import Artifact, DataPart, FilePart, FileWithBytes, FileWithUri, Message, Role, TextPart
from fastapi import status
from kink import inject
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
from agentstack_server.exceptions import EntityNotFoundError, PlatformError
from agentstack_server.service_layer.services.model_providers import ModelProviderService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.utils import filter_dict, utc_now

logger = logging.getLogger(__name__)


@inject
class ContextService:
    def __init__(
        self,
        uow: IUnitOfWorkFactory,
        configuration: Configuration,
        object_storage: IObjectStorageRepository,
        model_provider_service: ModelProviderService,
    ):
        self._uow = uow
        self._object_storage = object_storage
        self._configuration = configuration
        self._expire_resources_after = timedelta(days=configuration.context.resources_expire_after_days)
        self._model_provider_service = model_provider_service

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
            # File DB objects are deleted automatically using cascade

            # Vector stores
            # deleted automatically using cascade

            await uow.contexts.delete(context_id=context_id, user_id=user.id)
            await uow.commit()

        # TODO: a cronjob should sweep the files if the deletion fails here
        await self._object_storage.delete_files(file_ids=file_ids)

    async def expire_resources(self) -> dict[str, int]:
        if self._expire_resources_after <= timedelta(0):
            return {"files": 0, "vector_stores": 0}

        deleted_stats = {"files": 0, "vector_stores": 0}
        page_token = None
        has_more = True

        while has_more:
            file_ids = []
            async with self._uow() as uow:
                # TODO: mark contexts as cleaned up to filter them out in next cleanup
                page = await uow.contexts.list_paginated(
                    last_active_before=utc_now() - self._expire_resources_after,
                    page_token=page_token,
                    limit=100,
                )
                for context in page.items:
                    # Files
                    file_ids.extend([file.id async for file in uow.files.list(context_id=context.id)])
                    with suppress(EntityNotFoundError):
                        deleted_stats["files"] += await uow.files.delete(context_id=context.id)

                    # Vector stores
                    with suppress(EntityNotFoundError):
                        deleted_stats["vector_stores"] += await uow.vector_stores.delete(context_id=context.id)
                await uow.commit()

            page_token = page.next_page_token
            has_more = page.has_more

            # TODO: a cronjob should sweep the files if the deletion fails here
            await self._object_storage.delete_files(file_ids=file_ids)

        return deleted_stats

    async def update_last_active(self, *, context_id: UUID) -> None:
        async with self._uow() as uow:
            await uow.contexts.update_last_active(context_id=context_id)
            await uow.commit()

    def _extract_content_for_title(
        self, msg: Message | Artifact
    ) -> tuple[str, str | None, Sequence[FileWithUri | FileWithBytes]]:
        title_hint: str | None = None
        text_parts: list[str] = []
        files: list[FileWithUri | FileWithBytes] = []
        for part in msg.parts:
            match part.root:
                case TextPart(text=text):
                    text_parts.append(text)
                case DataPart(data={"title_hint": str(hint)}) if hint and not title_hint:
                    title_hint = hint
                case FilePart(file=file):
                    files.append(file)
                case _:
                    pass
        return "".join(text_parts), title_hint, files

    async def add_history_item(self, *, context_id: UUID, data: ContextHistoryItemData, user: User) -> None:
        async with self._uow() as uow:
            context = await uow.contexts.get(context_id=context_id, user_id=user.id)
            await uow.contexts.add_history_item(
                context_id=context_id,
                history_item=ContextHistoryItem(context_id=context_id, data=data),
            )

            if getattr(data, "role", None) == Role.user and not (context.metadata or {}).get("title"):
                from agentstack_server.jobs.tasks.context import generate_conversation_title as task

                # Use simple text extraction for the initial title placeholder
                title = self._extract_content_for_title(data)[0] or "Untitled"
                title = f"{title[:100]}..." if len(title) > 100 else title

                should_generate_title = self._configuration.generate_conversation_title.enabled
                state = TitleGenerationState.PENDING if should_generate_title else TitleGenerationState.COMPLETED
                await uow.contexts.update_title(context_id=context_id, title=title, generation_state=state)

                if should_generate_title:
                    await task.configure(queueing_lock=str(context_id)).defer_async(context_id=str(context_id))

            await uow.commit()

    async def generate_conversation_title(self, *, context_id: UUID):
        from jinja2 import Template

        async with self._uow() as uow:
            msg = await uow.contexts.list_history(context_id=context_id, limit=1, order="desc", order_by="created_at")
            system_config = await uow.configuration.get_system_configuration()

        model = self._configuration.generate_conversation_title.model
        if model == "default":
            if not system_config.default_llm_model:
                logger.warning(f"Cannot generate title for context {context_id}: default LLM model not set.")
                return
            model = system_config.default_llm_model

        if not msg.items:
            logger.warning(f"Cannot generate title for context {context_id}: no history found.")
            return

        raw_message = msg.items[0].data
        text, title_hint, files = self._extract_content_for_title(raw_message)
        if not text and not title_hint and not files:
            logger.warning(f"Cannot generate title for context {context_id}: first message has no content.")
            return

        try:
            # Render the system prompt using Jinja2
            template = Template(self._configuration.generate_conversation_title.prompt)
            prompt = template.render(
                text=text,
                titleHint=title_hint,
                files=[file.model_dump(include={"name", "mime_type"}) for file in files],
                rawMessage=raw_message.model_dump(),
            )
            resp = await self._model_provider_service.create_chat_completion(
                request=ChatCompletionRequest(
                    model=model,
                    stream=False,
                    max_completion_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
            )
            title = (resp.choices[0].message.content or "").strip().strip("\"'")
            title = f"{title[:100]}..." if len(title) > 100 else title
            if not title:
                raise RuntimeError("Generated title is empty.")
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
