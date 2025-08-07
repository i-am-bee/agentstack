# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.api.dependencies import AuthenticatedUserDependency, UserFeedbackServiceDependency
from beeai_server.api.schema.user_feedback import InsertUserFeedbackRequest

router = fastapi.APIRouter()


@router.post("", status_code=fastapi.status.HTTP_201_CREATED)
async def user_feedback(
    request: InsertUserFeedbackRequest,
    user_feedback_service: UserFeedbackServiceDependency,
    user: AuthenticatedUserDependency,
) -> None:
    await user_feedback_service.create_user_feedback(
        provider_id=request.provider_id,
        task_id=request.task_id,
        context_id=request.context_id,
        rating=request.rating,
        comment=request.comment,
        comment_tags=request.comment_tags,
        message=request.message,
        user=user,
    )
