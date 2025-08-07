# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import APIRouter, Depends, status

from beeai_server.api.auth import issue_internal_jwt
from beeai_server.api.dependencies import ConfigurationDependency, ContextServiceDependency, RequiresPermissions
from beeai_server.api.schema.common import EntityModel, PaginatedResponse
from beeai_server.api.schema.contexts import ContextTokenCreateRequest, ContextTokenResponse
from beeai_server.domain.models.context import Context
from beeai_server.domain.models.permissions import AuthorizedUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_context(
    context_service: ContextServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(contexts={"write"}))],
) -> EntityModel[Context]:
    return EntityModel(await context_service.create(user=user.user))


@router.get("")
async def list_contexts(
    context_service: ContextServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(contexts={"read"}))],
) -> PaginatedResponse[Context]:
    contexts = [context async for context in context_service.list(user=user.user)]
    return PaginatedResponse(items=contexts, total_count=len(contexts))


@router.get("/{context_id}")
async def get_context(
    context_id: UUID,
    context_service: ContextServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(contexts={"read"}))],
) -> EntityModel[Context]:
    return EntityModel(await context_service.get(context_id=context_id, user=user.user))


@router.delete("/{context_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_context(
    context_id: UUID,
    context_service: ContextServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(contexts={"write"}))],
) -> None:
    await context_service.delete(context_id=context_id, user=user.user)


@router.post("/{context_id}/token")
async def generate_context_token(
    context_id: UUID,
    request: ContextTokenCreateRequest,
    context_service: ContextServiceDependency,
    configuration: ConfigurationDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(contexts={"write"}))],
) -> ContextTokenResponse:
    if not user.active_permissions.check(request.grant_global_permissions | request.grant_context_permissions):
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempted to grant permissions you don't have",
        )
    # Verify user has access to this context
    await context_service.get(context_id=context_id, user=user.user)
    token, expires_at = issue_internal_jwt(
        user_id=user.user.id,
        context_id=context_id,
        global_permissions=request.grant_global_permissions,
        context_permissions=request.grant_context_permissions,
        configuration=configuration,
    )
    return ContextTokenResponse(token=token, expires_at=expires_at)
