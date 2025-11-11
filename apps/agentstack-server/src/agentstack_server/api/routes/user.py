# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from agentstack_server.api.dependencies import authorized_user
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_user(user: Annotated[AuthorizedUser, Depends(authorized_user)]) -> User:
    return user.user
