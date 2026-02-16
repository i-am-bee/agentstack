# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging

from kink import inject
from procrastinate import Blueprint

from agentstack_server import get_configuration
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.registry import (
    ModelProviderRegistryLocation,
    ModelProviderRegistryRecord,
)
from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.configurations import ConfigurationService
from agentstack_server.service_layer.services.model_providers import ModelProviderService
from agentstack_server.service_layer.services.users import UserService

logger = logging.getLogger(__name__)

blueprint = Blueprint()


async def update_system_configuration(
    configuration: Configuration, configuration_service: ConfigurationService, user_service: UserService
):
    if configuration.model_provider.default_llm_model or configuration.model_provider.default_embedding_model:
        user = await user_service.get_user_by_email("admin@beeai.dev")
        existing_configuration = await configuration_service.get_system_configuration(user=user)
        default_llm_model = configuration.model_provider.default_llm_model or existing_configuration.default_llm_model
        default_embedding_model = (
            configuration.model_provider.default_embedding_model or existing_configuration.default_embedding_model
        )
        should_update = (
            default_llm_model != existing_configuration.default_llm_model
            or default_embedding_model != existing_configuration.default_embedding_model
        )
        if should_update:
            _ = await configuration_service.update_system_configuration(
                default_llm_model=default_llm_model,
                default_embedding_model=default_embedding_model,
                user=await user_service.get_user(existing_configuration.created_by),
            )


# TODO: Can't use DI here because it's not initialized yet
# pyrefly: ignore [bad-argument-type] -- bad typing in blueprint library
@blueprint.periodic(cron=get_configuration().model_provider.update_models_period_cron)
@blueprint.task(queueing_lock="update_model_state_and_cache", queue=str(Queues.CRON_MODEL_PROVIDER))
@inject
async def update_model_state_and_cache(
    timestamp: int,
    model_provider_service: ModelProviderService,
    configuration: Configuration,
    configuration_service: ConfigurationService,
    user_service: UserService,
):
    await model_provider_service.update_model_state_and_cache()
    await update_system_configuration(configuration, configuration_service, user_service)


# TODO: Can't use DI here because it's not initialized yet
# pyrefly: ignore [bad-argument-type] -- bad typing in blueprint library
@blueprint.periodic(cron=get_configuration().model_provider_registry.sync_period_cron)
@blueprint.task(queueing_lock="check_model_provider_registry", queue=str(Queues.CRON_MODEL_PROVIDER))
@inject
async def check_model_provider_registry(
    timestamp: int,
    configuration: Configuration,
    model_provider_service: ModelProviderService,
    configuration_service: ConfigurationService,
    user_service: UserService,
):
    if not configuration.model_provider_registry.locations:
        return

    registry_by_provider_origin: dict[str, ModelProviderRegistryLocation] = {}
    desired_providers: dict[str, ModelProviderRegistryRecord] = {}
    errors = []

    for registry in configuration.model_provider_registry.locations.values():
        try:
            for provider_record in await registry.load():
                origin = str(provider_record.base_url)
                desired_providers[origin] = provider_record
                registry_by_provider_origin[origin] = registry
        except Exception as e:
            errors.append(e)

    # list_providers returns all providers. We filter for those that have a registry set.
    # Note: ModelProvider.registry is a RegistryLocation object.
    all_providers = await model_provider_service.list_providers()
    managed_providers = {str(provider.base_url): provider for provider in all_providers if provider.registry}

    new_providers = desired_providers.keys() - managed_providers.keys()
    old_providers = managed_providers.keys() - desired_providers.keys()

    # Remove old providers
    for provider_origin in old_providers:
        provider = managed_providers[provider_origin]
        try:
            await model_provider_service.delete_provider(model_provider_id=provider.id, allow_registry_update=True)
            logger.info(f"Removed model provider {provider.base_url}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider.base_url}]: Failed to remove model provider: {ex}"))

    # Update existing providers
    existing_providers = desired_providers.keys() & managed_providers.keys()
    for provider_origin in existing_providers:
        provider = managed_providers[provider_origin]
        provider_record = desired_providers[provider_origin]

        try:
            await model_provider_service.patch_provider(
                model_provider_id=provider.id,
                name=provider_record.name,
                description=provider_record.description,
                type=provider_record.type,
                base_url=provider_record.base_url,
                api_key=provider_record.api_key,
                watsonx_project_id=provider_record.watsonx_project_id,
                watsonx_space_id=provider_record.watsonx_space_id,
                allow_registry_update=True,
            )
            logger.info(f"Updated model provider {provider.base_url}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider.base_url}]: Failed to update model provider: {ex}"))

    # Add new providers
    for provider_origin in new_providers:
        provider_record = desired_providers[provider_origin]
        try:
            new_provider = await model_provider_service.create_provider(
                name=provider_record.name,
                description=provider_record.description,
                type=provider_record.type,
                base_url=provider_record.base_url,
                api_key=provider_record.api_key,
                watsonx_project_id=provider_record.watsonx_project_id,
                watsonx_space_id=provider_record.watsonx_space_id,
                registry=registry_by_provider_origin[provider_origin],
            )
            logger.info(f"Added model provider {new_provider.base_url}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider_record.base_url}]: Failed to add model provider: {ex}"))

    try:
        await update_system_configuration(configuration, configuration_service, user_service)
    except Exception as ex:
        errors.append(RuntimeError(f"Failed to update system configuration: {ex}"))

    if errors:
        raise ExceptionGroup("Exceptions occurred when reloading model providers", errors)
