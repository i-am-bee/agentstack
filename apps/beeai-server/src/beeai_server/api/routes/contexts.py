# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import APIRouter, Depends, status

from beeai_server.api.auth import issue_internal_jwt
from beeai_server.api.dependencies import (
    ConfigurationDependency,
    ContextServiceDependency,
    RequiresContextPermissionsPath,
    RequiresPermissions,
)
from beeai_server.api.schema.common import EntityModel, PaginatedResponse
from beeai_server.api.schema.contexts import (
    ContextHistoryItemCreateRequest,
    ContextTokenCreateRequest,
    ContextTokenResponse,
)
from beeai_server.domain.models.context import Context, ContextHistoryItem
from beeai_server.domain.models.permissions import AuthorizedUser, Permissions

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
    global_grant = Permissions.model_validate(request.grant_global_permissions.model_dump(serialize_as_any=True))
    context_grant = Permissions.model_validate(request.grant_context_permissions.model_dump(serialize_as_any=True))

    if user.token_context_id:
        raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN, "Context tokens cannot be used to generate other tokens")

    if (global_grant | context_grant).check(Permissions(contexts={"write"})):
        raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN, "Cannot grant permissions to generate a token")

    if not user.global_permissions.check(global_grant | context_grant):
        raise fastapi.HTTPException(status.HTTP_400_BAD_REQUEST, "Attempted to grant permissions you don't have")

    # Verify user has access to this context
    await context_service.get(context_id=context_id, user=user.user)

    token, expires_at = issue_internal_jwt(
        user_id=user.user.id,
        context_id=context_id,
        global_permissions=global_grant,
        context_permissions=context_grant,
        configuration=configuration,
    )
    return ContextTokenResponse(token=token, expires_at=expires_at)


@router.post("/{context_id}/history", status_code=status.HTTP_201_CREATED)
async def add_context_history_item(
    context_id: UUID,
    history_item: ContextHistoryItemCreateRequest,
    context_service: ContextServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissionsPath(context_data={"write"}))],
) -> None:
    # Cannot add history to a different context
    if user.context_id and user.context_id != context_id:
        raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    await context_service.add_history_item(context_id=context_id, history_item=history_item.root, user=user.user)


@router.get("/{context_id}/history")
async def list_context_history(
    context_id: UUID,
    context_service: ContextServiceDependency,
    user: Annotated[AuthorizedUser, Depends(RequiresContextPermissionsPath(context_data={"read"}))],
) -> PaginatedResponse[ContextHistoryItem]:
    # Cannot list history for a different context
    if user.context_id and user.context_id != context_id:
        raise fastapi.HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
    history = [item async for item in context_service.list_history(context_id=context_id, user=user.user)]
    return PaginatedResponse(items=history, total_count=len(history))
