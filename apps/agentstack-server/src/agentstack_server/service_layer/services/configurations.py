# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging

from kink import inject

from agentstack_server.domain.models.configuration import SystemConfiguration
from agentstack_server.domain.models.user import User
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.service_layer.services.model_providers import ModelProviderService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)


@inject
class ConfigurationService:
    def __init__(self, uow: IUnitOfWorkFactory, model_provider_service: ModelProviderService):
        self._uow = uow
        self._model_provider_service = model_provider_service

    async def get_system_configuration(self, *, user: User) -> SystemConfiguration:
        """Get the current system configuration."""
        async with self._uow() as uow:
            try:
                return await uow.configuration.get_system_configuration()
            except EntityNotFoundError:
                return SystemConfiguration(created_by=user.id)

    async def update_system_configuration(
        self,
        *,
        default_llm_model: str | None = None,
        default_embedding_model: str | None = None,
        user: User,
    ) -> SystemConfiguration:
        configuration = SystemConfiguration(
            default_llm_model=default_llm_model, default_embedding_model=default_embedding_model, created_by=user.id
        )

        if default_llm_model:
            # check provider exists
            await self._model_provider_service.get_provider_by_model_id(model_id=default_llm_model)

        if default_embedding_model:
            # check provider exists
            await self._model_provider_service.get_provider_by_model_id(model_id=default_embedding_model)

        async with self._uow() as uow:
            await uow.configuration.create_or_update_system_configuration(configuration=configuration)
            await uow.commit()

        return configuration
