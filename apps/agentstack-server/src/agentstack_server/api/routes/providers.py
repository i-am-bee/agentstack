# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import HTTPException, status
from fastapi.params import Depends, Query
from fastapi.requests import Request
from pydantic import TypeAdapter

from agentstack_server.api.dependencies import (
    ConfigurationDependency,
    ProviderServiceDependency,
    RequiresPermissions,
)
from agentstack_server.api.routes.a2a import create_proxy_agent_card
from agentstack_server.api.schema.common import EntityModel
from agentstack_server.api.schema.provider import CreateProviderRequest
from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.domain.models.provider import Provider, ProviderLocation

router = fastapi.APIRouter()


@router.post("")
async def create_provider(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
) -> Provider:
    return await provider_service.create_provider(
        user=user.user,
        location=request.location,
        origin=request.origin,
        agent_card=request.agent_card,
    )


@router.post("/preview")
async def preview_provider(
    request: CreateProviderRequest,
    provider_service: ProviderServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
) -> Provider:
    return await provider_service.preview_provider(location=request.location, agent_card=request.agent_card)


@router.get("")
async def list_providers(
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    request: Request,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}), use_cache=False)],
    user_owned: Annotated[bool | None, Query()] = None,
    origin: Annotated[str | None, Query()] = None,
) -> PaginatedResult[EntityModel[Provider]]:
    providers = []
    for provider in await provider_service.list_providers(user=user.user, user_owned=user_owned, origin=origin):
        new_provider = provider.model_copy(
            update={
                "agent_card": create_proxy_agent_card(
                    provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
                )
            }
        )
        providers.append(
            # pyrefly: ignore [bad-argument-type] -- TODO: fix the EntityModel hack so that both Pyrefly and FastAPI understand it
            EntityModel(new_provider)
        )

    return PaginatedResult(items=providers, total_count=len(providers))


@router.get("/{id}")
async def get_provider(
    id: UUID,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    request: Request,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}))],
) -> EntityModel[Provider]:
    provider = await provider_service.get_provider(provider_id=id)
    return EntityModel(  # pyrefly: ignore [bad-return] -- TODO: fix the EntityModel hack so that both Pyrefly and FastAPI understand it
        provider.model_copy(
            update={
                "agent_card": create_proxy_agent_card(
                    provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
                )
            }
        )
    )


@router.get("/by-location/{location:path}")
async def get_provider_by_location(
    location: str,
    provider_service: ProviderServiceDependency,
    configuration: ConfigurationDependency,
    request: Request,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}))],
) -> EntityModel[Provider]:
    try:
        parsed_location: ProviderLocation = TypeAdapter(ProviderLocation).validate_python(location)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    provider = await provider_service.get_provider(location=parsed_location)
    return EntityModel(  # pyrefly: ignore [bad-return] -- TODO: fix the EntityModel hack so that both Pyrefly and FastAPI understand it
        provider.model_copy(
            update={
                "agent_card": create_proxy_agent_card(
                    provider.agent_card, provider_id=provider.id, request=request, configuration=configuration
                )
            }
        )
    )


@router.delete("/{id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_provider(
    id: UUID,
    provider_service: ProviderServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
) -> None:
    # admin can delete any provider, other users only their providers
    await provider_service.delete_provider(provider_id=id, user=user.user)


