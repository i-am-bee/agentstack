# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import fastapi

from beeai_server.api.routes.dependencies import EnvServiceDependency, AdminAuthDependency
from beeai_server.api.schema.env import UpdateVariablesRequest, ListVariablesSchema

router = fastapi.APIRouter()


@router.put("", status_code=fastapi.status.HTTP_201_CREATED)
async def update_variables(
    request: UpdateVariablesRequest, env_service: EnvServiceDependency, _: AdminAuthDependency
) -> None:
    await env_service.update_env(env=request.env)


@router.get("")
async def list_variables(env_service: EnvServiceDependency, _: AdminAuthDependency) -> ListVariablesSchema:
    return ListVariablesSchema(env=await env_service.list_env())
