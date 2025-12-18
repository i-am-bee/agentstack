# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import UUID

from kink import inject

from agentstack_server.domain.models.user import User, UserRole
from agentstack_server.domain.models.user_feedback import UserFeedback
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class UserFeedbackService:
    def __init__(self, uow: IUnitOfWorkFactory):
        self._uow = uow

    async def create_user_feedback(
        self,
        *,
        provider_id: UUID,
        rating: int,
        comment: str | None = None,
        comment_tags: list[str] | None = None,
        message: str,
        task_id: UUID,
        context_id: UUID,
        user: User,
    ):
        async with self._uow() as uow:
            try:
                task = await uow.a2a_requests.get_task(task_id=str(task_id), user_id=user.id)
                trace_id = task.trace_id
            except EntityNotFoundError:
                trace_id = None

            user_feedback = UserFeedback(
                provider_id=provider_id,
                rating=rating,
                comment=comment,
                comment_tags=comment_tags,
                message=message,
                task_id=task_id,
                context_id=context_id,
                created_by=user.id,
                trace_id=trace_id,
            )
            await uow.user_feedback.create(user_feedback=user_feedback)
            await uow.commit()
            return user_feedback

    async def list_user_feedback(
        self,
        *,
        user: User,
        provider_id: UUID | None = None,
        limit: int = 50,
        after_cursor: UUID | None = None,
    ) -> tuple[list[UserFeedback], int, bool]:
        if user.role not in (UserRole.ADMIN, UserRole.DEVELOPER):
            raise ValueError("Listing feedback is only allowed for admins and developers")

        provider_created_by = user.id if user.role == UserRole.DEVELOPER else None

        async with self._uow() as uow:
            feedback_list, total, has_more = await uow.user_feedback.list(
                provider_created_by=provider_created_by,
                provider_id=provider_id,
                limit=limit,
                after_cursor=after_cursor,
            )
            return feedback_list, total, has_more
