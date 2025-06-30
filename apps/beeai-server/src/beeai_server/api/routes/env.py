# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.api.dependencies import EnvServiceDependency, AdminUserDependency
from beeai_server.api.schema.env import UpdateVariablesRequest, ListVariablesSchema

router = fastapi.APIRouter()


@router.put("", status_code=fastapi.status.HTTP_201_CREATED)
async def update_variables(
    request: UpdateVariablesRequest, env_service: EnvServiceDependency, _: AdminUserDependency
) -> None:
    await env_service.update_env(env=request.env)


@router.get("")
async def list_variables(env_service: EnvServiceDependency, _: AdminUserDependency) -> ListVariablesSchema:
    return ListVariablesSchema(env=await env_service.list_env())
