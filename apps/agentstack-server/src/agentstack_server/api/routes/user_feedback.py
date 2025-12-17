# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends, Query

from agentstack_server.api.dependencies import (
    RequiresPermissions,
    UserFeedbackServiceDependency,
)
from agentstack_server.api.schema.user_feedback import (
    InsertUserFeedbackRequest,
    ListUserFeedbackResponse,
    UserFeedbackResponse,
)
from agentstack_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()


@router.post("", status_code=fastapi.status.HTTP_201_CREATED)
async def user_feedback(
    request: InsertUserFeedbackRequest,
    user_feedback_service: UserFeedbackServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(feedback={"write"}))],
) -> None:
    await user_feedback_service.create_user_feedback(
        provider_id=request.provider_id,
        task_id=request.task_id,
        context_id=request.context_id,
        rating=request.rating,
        comment=request.comment,
        comment_tags=request.comment_tags,
        message=request.message,
        user=user.user,
    )


@router.get("", status_code=fastapi.status.HTTP_200_OK)
async def list_user_feedback(
    user_feedback_service: UserFeedbackServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(feedback={"read"}))],
    provider_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    after_cursor: Annotated[UUID | None, Query()] = None,
) -> ListUserFeedbackResponse:
    feedback_list, total, has_more = await user_feedback_service.list_user_feedback(
        user=user.user,
        provider_id=provider_id,
        limit=limit,
        after_cursor=after_cursor,
    )
    return ListUserFeedbackResponse(
        items=[UserFeedbackResponse.model_validate(dict(feedback)) for feedback in feedback_list],
        total_count=total,
        has_more=has_more,
    )
