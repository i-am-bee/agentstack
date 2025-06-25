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
from fastapi import HTTPException, status
from fastapi.params import Query

from beeai_server.api.schema.provider import CreateProviderRequest
from uuid import UUID

from beeai_server.domain.models.provider import ProviderWithState
from beeai_server.api.dependencies import ProviderServiceDependency, AdminUserDependency, ConfigurationDependency
from beeai_server.api.schema.common import PaginatedResponse
from starlette.responses import StreamingResponse

from beeai_server.utils.fastapi import streaming_response

router = fastapi.APIRouter()


@router.post("")
async def create_provider(
    _: AdminUserDependency,
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    auto_remove: bool = Query(default=False),
) -> ProviderWithState:
    if auto_remove and not configuration.provider.auto_remove_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auto remove functionality is disabled")
    return await provider_service.create_provider(
        location=request.location, agents=request.agents, auto_remove=auto_remove
    )


@router.post("/preview")
async def preview_provider(
    request: CreateProviderRequest, provider_service: ProviderServiceDependency
) -> ProviderWithState:
    return await provider_service.preview_provider(location=request.location, agents=request.agents)


@router.get("")
async def list_providers(provider_service: ProviderServiceDependency) -> PaginatedResponse[ProviderWithState]:
    providers = await provider_service.list_providers()
    return PaginatedResponse(items=providers, total_count=len(providers))


@router.get("/{id}")
async def get_provider(id: UUID, provider_service: ProviderServiceDependency) -> ProviderWithState:
    return await provider_service.get_provider(provider_id=id)


@router.delete("/{id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_provider(
    _: AdminUserDependency,
    id: UUID,
    provider_service: ProviderServiceDependency,
) -> None:
    await provider_service.delete_provider(provider_id=id)


@router.get("/{id}/logs", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def stream_logs(
    _: AdminUserDependency,
    id: UUID,
    provider_service: ProviderServiceDependency,
) -> StreamingResponse:
    logs_iterator = await provider_service.stream_logs(provider_id=id)
    return streaming_response(logs_iterator())
