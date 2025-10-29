# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import UUID

from kink import inject

from agentstack_server.domain.models.user import User
from agentstack_server.domain.models.user_feedback import UserFeedback
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
            user_feedback = UserFeedback(
                provider_id=provider_id,
                rating=rating,
                comment=comment,
                comment_tags=comment_tags,
                message=message,
                task_id=task_id,
                context_id=context_id,
                created_by=user.id,
            )
            await uow.user_feedback.create(user_feedback=user_feedback)
            await uow.commit()
            return user_feedback
