# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated

import fastapi
from fastapi import APIRouter, Depends

from beeai_server.api.dependencies import RequiresPermissions, UserServiceDependency
from beeai_server.api.schema.env import ListVariablesSchema, UpdateVariablesRequest
from beeai_server.domain.models.permissions import AuthorizedUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put("", status_code=fastapi.status.HTTP_201_CREATED)
async def update_user_variables(
    request: UpdateVariablesRequest,
    user_service: UserServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(variables={"write"}))],
) -> None:
    await user_service.update_user_env(user=user.user, env=request.variables)


@router.get("")
async def list_user_variables(
    user_service: UserServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(variables={"read"}))],
) -> ListVariablesSchema:
    return ListVariablesSchema(variables=await user_service.list_user_env(user=user.user))
