# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

import fastapi
from fastapi import Depends

from beeai_server.api.dependencies import EnvServiceDependency, RequiresPermissions
from beeai_server.api.schema.env import ListVariablesSchema, UpdateVariablesRequest
from beeai_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()


@router.put("", status_code=fastapi.status.HTTP_201_CREATED)
async def update_variables(
    request: UpdateVariablesRequest,
    env_service: EnvServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(variables={"write"}))],
) -> None:
    await env_service.update_env(env=request.env)


@router.get("")
async def list_variables(
    env_service: EnvServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(variables={"read"}))],
) -> ListVariablesSchema:
    return ListVariablesSchema(env=await env_service.list_env())
