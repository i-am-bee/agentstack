# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from agentstack_server.api.dependencies import authorized_user
from agentstack_server.api.schema.user import UserResponse
from agentstack_server.domain.models.permissions import AuthorizedUser

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("/me")
async def get_me(user: Annotated[AuthorizedUser, Depends(authorized_user)]) -> UserResponse:
    """Get current user"""
    return UserResponse.model_validate(user.user.model_dump())
