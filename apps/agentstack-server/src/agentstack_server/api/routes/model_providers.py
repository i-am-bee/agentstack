# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends, status

from agentstack_server.api.dependencies import (
    ModelProviderServiceDependency,
    RequiresPermissions,
)
from agentstack_server.api.schema.common import EntityModel
from agentstack_server.api.schema.model_provider import CreateModelProviderRequest, MatchModelsRequest
from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.model_provider import ModelProvider, ModelWithScore
from agentstack_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_model_provider(
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"write"}))],
    request: CreateModelProviderRequest,
    model_provider_service: ModelProviderServiceDependency,
) -> EntityModel[ModelProvider]:
    model_provider = await model_provider_service.create_provider(
        name=request.name,
        description=request.description,
        type=request.type,
        base_url=request.base_url,
        watsonx_project_id=request.watsonx_project_id,
        watsonx_space_id=request.watsonx_space_id,
        api_key=request.api_key.get_secret_value(),
    )
    return EntityModel(model_provider)


@router.get("")
async def list_model_providers(
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"read"}))],
    model_provider_service: ModelProviderServiceDependency,
) -> PaginatedResult[ModelProvider]:
    providers = await model_provider_service.list_providers()
    return PaginatedResult(items=providers, total_count=len(providers))


@router.get("/{model_provider_id}")
async def get_model_provider(
    model_provider_id: UUID,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"read"}))],
    model_provider_service: ModelProviderServiceDependency,
) -> EntityModel[ModelProvider]:
    provider = await model_provider_service.get_provider(model_provider_id=model_provider_id)
    return EntityModel(provider)


@router.delete("/{model_provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_provider(
    model_provider_id: UUID,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"write"}))],
    model_provider_service: ModelProviderServiceDependency,
) -> None:
    await model_provider_service.delete_provider(model_provider_id=model_provider_id)


@router.post("/match")
async def match(
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"read"}))],
    request: MatchModelsRequest,
    model_provider_service: ModelProviderServiceDependency,
) -> PaginatedResult[ModelWithScore]:
    models = await model_provider_service.match_models(
        suggested_models=request.suggested_models,
        capability=request.capability,
        score_cutoff=request.score_cutoff,
    )
    return PaginatedResult(items=models, total_count=len(models))
