# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from starlette.responses import StreamingResponse

from beeai_server.api.dependencies import (
    ProviderBuildServiceDependency,
    RequiresPermissions,
)
from beeai_server.api.schema.provider_build import CreateProviderBuildRequest
from beeai_server.configuration import get_configuration
from beeai_server.domain.models.common import PaginatedResult
from beeai_server.domain.models.permissions import AuthorizedUser
from beeai_server.domain.models.provider_build import ProviderBuild
from beeai_server.utils.fastapi import streaming_response

router = fastapi.APIRouter()

if get_configuration().features.provider_builds:

    @router.post("")
    async def create_provider_build(
        user: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        request: CreateProviderBuildRequest,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> ProviderBuild:
        return await provider_build_service.create_build(location=request.location, user=user.user)

    @router.get("/{id}")
    async def get_provider_build(
        _: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"read"}))],
        id: UUID,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> ProviderBuild:
        return await provider_build_service.get_build(provider_build_id=id)

    @router.get("")
    async def list_provider_build(
        _: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"read"}))],
        provider_build_service: ProviderBuildServiceDependency,
    ) -> PaginatedResult[ProviderBuild]:
        return await provider_build_service.list_builds()

    @router.get("/{id}/logs")
    async def stream_logs(
        _: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        id: UUID,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> StreamingResponse:
        logs_iterator = await provider_build_service.stream_logs(provider_build_id=id)
        return streaming_response(logs_iterator())

    @router.delete("/{id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
    async def delete(
        _: Annotated[AuthorizedUser, Depends(RequiresPermissions(provider_builds={"write"}))],
        id: UUID,
        provider_build_service: ProviderBuildServiceDependency,
    ) -> None:
        await provider_build_service.delete_build(provider_build_id=id)
