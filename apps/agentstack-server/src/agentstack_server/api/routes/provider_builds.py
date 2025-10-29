# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends, Query
from starlette.responses import StreamingResponse

from agentstack_server.api.dependencies import (
    ProviderBuildServiceDependency,
    RequiresPermissions,
)
from agentstack_server.api.schema.provider_build import CreateProviderBuildRequest, ProviderBuildListQuery
from agentstack_server.configuration import get_configuration
from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.domain.models.provider_build import ProviderBuild
from agentstack_server.utils.fastapi import streaming_response

router = fastapi.APIRouter()

if get_configuration().features.provider_builds:

    @router.post("")
    async def create_provider_build(
        user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        request: CreateProviderBuildRequest,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> ProviderBuild:
        return await provider_build_service.create_build(
            location=request.location,
            user=user.user,
            on_complete=request.on_complete,
            build_configuration=request.build_configuration,
        )

    @router.post("/preview")
    async def preview_provider_build(
        user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        request: CreateProviderBuildRequest,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> ProviderBuild:
        return await provider_build_service.preview_build(
            location=request.location, user=user.user, on_complete=request.on_complete
        )

    @router.get("/{id}")
    async def get_provider_build(
        _: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"read"}))],
        id: UUID,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> ProviderBuild:
        return await provider_build_service.get_build(provider_build_id=id)

    @router.get("")
    async def list_provider_builds(
        user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"read"}))],
        provider_build_service: ProviderBuildServiceDependency,
        query: Annotated[ProviderBuildListQuery, Query()],
    ) -> PaginatedResult[ProviderBuild]:
        return await provider_build_service.list_builds(
            pagination=query,
            status=query.status,
            user=user.user,
            user_owned=query.user_owned,
        )

    @router.get("/{id}/logs")
    async def stream_logs(
        user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        id: UUID,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> StreamingResponse:
        # admin can see logs from all builds, other users only logs of their build
        logs_iterator = await provider_build_service.stream_logs(provider_build_id=id, user=user.user)
        return streaming_response(logs_iterator())

    @router.delete("/{id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
    async def delete(
        user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        id: UUID,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> None:
        # admin can delete all builds, other users only their build
        await provider_build_service.delete_build(provider_build_id=id, user=user.user)
