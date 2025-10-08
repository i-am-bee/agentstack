# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from datetime import timedelta
from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import HTTPException, status
from fastapi.params import Depends, Query
from fastapi.requests import Request
from starlette.responses import StreamingResponse

from beeai_server.api.dependencies import (
    ConfigurationDependency,
    ProviderServiceDependency,
    RequiresPermissions,
)
from beeai_server.api.routes.a2a import create_proxy_agent_card
from beeai_server.api.schema.env import ListVariablesSchema, UpdateVariablesRequest
from beeai_server.api.schema.provider import CreateProviderRequest
from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.permissions import AuthorizedUser
from beeai_server.domain.models.provider import ProviderWithState
from beeai_server.utils.fastapi import streaming_response

router = fastapi.APIRouter()


@router.post("")
async def create_provider(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    auto_remove: Annotated[bool, Query()] = False,
) -> ProviderWithState:
    if auto_remove and not configuration.provider.auto_remove_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auto remove functionality is disabled")
    return await provider_service.create_provider(
        user=user.user,
        auto_stop_timeout=timedelta(seconds=request.auto_stop_timeout_sec),
        location=request.location,
        agent_card=request.agent_card,
        auto_remove=auto_remove,
        variables=request.variables,
    )


@router.post("/preview")
async def preview_provider(
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
) -> ProviderWithState:
    return await provider_service.preview_provider(location=request.location, agent_card=request.agent_card)


@router.get("")
async def list_providers(
    provider_service: ProviderServiceDependency,
    request: Request,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}), use_cache=False)],
    user_owned: Annotated[bool, Query()] = False,
) -> PaginatedResult[ProviderWithState]:
    providers = []
    for provider in await provider_service.list_providers(user=user.user if user_owned else None):
        new_provider = provider.model_copy(
            update={
                "agent_card": create_proxy_agent_card(provider.agent_card, provider_id=provider.id, request=request)
            }
        )
        providers.append(new_provider)

    return PaginatedResult(items=providers, total_count=len(providers))


@router.get("/{id}")
async def get_provider(
    id: UUID,
    provider_service: ProviderServiceDependency,
    request: Request,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}))],
) -> ProviderWithState:
    provider = await provider_service.get_provider(provider_id=id)
    return provider.model_copy(
        update={"agent_card": create_proxy_agent_card(provider.agent_card, provider_id=provider.id, request=request)}
    )


@router.delete("/{id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_provider(
    id: UUID,
    provider_service: ProviderServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
) -> None:
    # admin can delete any provider, other users only their providers
    await provider_service.delete_provider(provider_id=id, user=user.user)


@router.get("/{id}/logs")
async def stream_logs(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
    id: UUID,
    provider_service: ProviderServiceDependency,
) -> StreamingResponse:
    # admin can see logs from all providers, other users only logs of their provider
    logs_iterator = await provider_service.stream_logs(provider_id=id, user=user.user)
    return streaming_response(logs_iterator())


@router.put("/{id}/variables", status_code=fastapi.status.HTTP_201_CREATED)
async def update_provider_variables(
    id: UUID,
    request: UpdateVariablesRequest,
    provider_service: ProviderServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_variables={"write"}))],
) -> None:
    # admin can update all variables, other users only variables of their provider
    await provider_service.update_provider_env(provider_id=id, env=request.variables, user=user.user)


@router.get("/{id}/variables")
async def list_provider_variables(
    id: UUID,
    provider_service: ProviderServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_variables={"read"}))],
) -> ListVariablesSchema:
    # admin can see all variables, other users only variables of their provider
    return ListVariablesSchema(variables=await provider_service.list_provider_env(provider_id=id, user=user.user))
