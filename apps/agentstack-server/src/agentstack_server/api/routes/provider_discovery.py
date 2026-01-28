# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends

from agentstack_server.api.dependencies import ProviderDiscoveryServiceDependency, RequiresPermissions
from agentstack_server.api.schema.provider_discovery import CreateDiscoveryRequest
from agentstack_server.domain.models.permissions import AuthorizedUser
from agentstack_server.domain.models.provider_discovery import ProviderDiscovery

router = fastapi.APIRouter()


@router.post("")
async def create_provider_discovery(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"write"}))],
    request: CreateDiscoveryRequest,
    service: ProviderDiscoveryServiceDependency,
) -> ProviderDiscovery:
    return await service.create_discovery(docker_image=request.docker_image, user=user.user)


@router.get("/{id}")
async def get_provider_discovery(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(providers={"read"}))],
    id: UUID,
    service: ProviderDiscoveryServiceDependency,
) -> ProviderDiscovery:
    return await service.get_discovery(discovery_id=id, user=user.user)
