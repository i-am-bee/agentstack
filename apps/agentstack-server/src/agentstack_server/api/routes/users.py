# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from agentstack_server.api.dependencies import UserServiceDependency, authorized_user
from agentstack_server.api.schema.user import ChangeRoleRequest, ChangeRoleResponse, UserListQuery, UserResponse
from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.domain.models.user import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("", response_model=PaginatedResult[UserResponse])
async def list_users(
    query: Annotated[UserListQuery, Query()],
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
    user_service: UserServiceDependency,
) -> PaginatedResult[UserResponse]:
    if not user.user.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")

    result = await user_service.list_users(
        limit=query.limit,
        page_token=query.page_token,
        email=query.email,
    )

    return PaginatedResult(
        items=[UserResponse(**u.model_dump()) for u in result.items],
        total_count=result.total_count,
        has_more=result.has_more,
    )


@router.put("/{user_id}/role", response_model=ChangeRoleResponse)
async def change_user_role(
    user_id: UUID,
    request: ChangeRoleRequest,
    user: Annotated[AuthorizedUser, Depends(authorized_user)],
    user_service: UserServiceDependency,
) -> ChangeRoleResponse:
    if not user.user.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")

    if user_id == user.user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change own role")

    updated_user = await user_service.change_role(user_id=user_id, new_role=request.new_role)

    return ChangeRoleResponse(
        user_id=updated_user.id,
        new_role=updated_user.role,
    )
