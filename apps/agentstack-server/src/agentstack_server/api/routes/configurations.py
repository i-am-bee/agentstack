# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

import fastapi
from fastapi import Depends

from agentstack_server.api.dependencies import (
    ConfigurationDependency,
    ConfigurationServiceDependency,
    RequiresPermissions,
)
from agentstack_server.api.schema.common import EntityModel
from agentstack_server.api.schema.configuration import UpdateConfigurationRequest
from agentstack_server.domain.models.configuration import SystemConfiguration
from agentstack_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()


@router.get("/system")
async def get_configuration(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(system_configuration={"read"}))],
    configuration_service: ConfigurationServiceDependency,
) -> EntityModel[SystemConfiguration]:
    configuration = await configuration_service.get_system_configuration(user=user.user)
    return EntityModel(configuration)


@router.put("/system")
async def update_configuration(
    user: Annotated[AuthorizedUser, Depends(RequiresPermissions(system_configuration={"write"}))],
    request: UpdateConfigurationRequest,
    configuration_service: ConfigurationServiceDependency,
    configuration: ConfigurationDependency,
) -> EntityModel[SystemConfiguration]:
    error_msg = "Default {model_type} model is configured via deployment and cannot be changed through API."
    config_llm = configuration.model_provider.default_llm_model
    config_embed = configuration.model_provider.default_embedding_model
    if config_llm and request.default_llm_model != config_llm:
        raise fastapi.HTTPException(status_code=400, detail=error_msg.format(model_type="LLM"))

    if config_embed and request.default_embedding_model != config_embed:
        raise fastapi.HTTPException(status_code=400, detail=error_msg.format(model_type="embedding"))

    result = await configuration_service.update_system_configuration(
        default_llm_model=request.default_llm_model,
        default_embedding_model=request.default_embedding_model,
        user=user.user,
    )

    return EntityModel(result)
