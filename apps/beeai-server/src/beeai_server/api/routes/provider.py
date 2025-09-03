# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
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
from beeai_server.api.schema.common import PaginatedResponse
from beeai_server.api.schema.provider import CreateProviderRequest
from beeai_server.domain.models.permissions import AuthorizedUser
from beeai_server.domain.models.provider import ProviderWithState
from beeai_server.utils.fastapi import streaming_response

router = fastapi.APIRouter()


@router.post("")
async def create_provider(
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    auto_remove: Annotated[bool, Query()] = False,
) -> ProviderWithState:
    if auto_remove and not configuration.provider.auto_remove_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auto remove functionality is disabled")
    return await provider_service.create_provider(
        location=request.location, agent_card=request.agent_card, auto_remove=auto_remove
    )


@router.post("/preview")
async def preview_provider(
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions())],
) -> ProviderWithState:
    return await provider_service.preview_provider(location=request.location, agent_card=request.agent_card)


@router.get("")
async def list_providers(
    provider_service: ProviderServiceDependency,
    request: Request,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}), use_cache=False)],
) -> PaginatedResponse[ProviderWithState]:
    providers = []
    for provider in await provider_service.list_providers():
        new_provider = provider.model_copy(
            update={
                "agent_card": create_proxy_agent_card(provider.agent_card, provider_id=provider.id, request=request)
            }
        )
        providers.append(new_provider)

    return PaginatedResponse(items=providers, total_count=len(providers))


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
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
) -> None:
    await provider_service.delete_provider(provider_id=id)


@router.get("/{id}/logs", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def stream_logs(
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
    id: UUID,
    provider_service: ProviderServiceDependency,
) -> StreamingResponse:
    logs_iterator = await provider_service.stream_logs(provider_id=id)
    return streaming_response(logs_iterator())
