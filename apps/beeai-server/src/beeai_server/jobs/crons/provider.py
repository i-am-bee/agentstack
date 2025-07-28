# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import suppress
from datetime import timedelta

import anyio
import httpx
from kink import inject
from procrastinate import Blueprint

from beeai_server import get_configuration
from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import Provider
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.service_layer.services.provider import ProviderService
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)

blueprint = Blueprint()


@blueprint.periodic(cron="*/1 * * * *")
@blueprint.task(queueing_lock="scale_down_providers", queue="cron:provider")
@inject
async def scale_down_providers(timestamp: int, service: ProviderService):
    await service.scale_down_providers()


# TODO: Can't use DI here because it's not initialized yet
@blueprint.periodic(cron=get_configuration().agent_registry.sync_period_cron)
@blueprint.task(queueing_lock="check_registry", queue="cron:provider")
@inject
async def check_registry(timestamp: int, configuration: Configuration, provider_service: ProviderService):
    if not configuration.agent_registry.locations:
        return

    registry_by_provider_id = {}
    desired_providers = {}
    errors = []

    for registry in configuration.agent_registry.locations.values():
        for provider_location in await registry.load():
            try:
                provider_id = Provider(
                    source=provider_location, env=[]
                ).id  # dummy object to calculate ID from location
                desired_providers[provider_id] = provider_location
                registry_by_provider_id[provider_id] = registry
            except ValueError as e:
                errors.append(e)

    managed_providers = {
        provider.id: provider for provider in await provider_service.list_providers() if provider.registry
    }

    new_providers = desired_providers.keys() - managed_providers.keys()
    old_providers = managed_providers.keys() - desired_providers.keys()

    # Remove old providers - to prevent agent name collisions
    for provider_id in old_providers:
        provider = managed_providers[provider_id]
        try:
            await provider_service.delete_provider(provider_id=provider.id)
            logger.info(f"Removed provider {provider.source}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider.source}]: Failed to remove provider: {ex}"))

    for provider_id in new_providers:
        provider_location = desired_providers[provider_id]
        try:
            await provider_service.create_provider(
                location=provider_location,
                registry=registry_by_provider_id[provider_id],
            )
            logger.info(f"Added provider {provider_location}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider_location}]: Failed to add provider: {ex}"))

    if errors:
        raise ExceptionGroup("Exceptions occurred when reloading providers", errors)


if get_configuration().provider.auto_remove_enabled:

    @blueprint.periodic(cron="* * * * * */5")
    @blueprint.task(queueing_lock="auto_remove_providers", queue="cron:provider")
    @inject
    async def auto_remove_providers(timestamp: int, uow_f: IUnitOfWorkFactory, provider_service: ProviderService):
        async with uow_f() as uow:
            auto_remove_providers = [provider async for provider in uow.providers.list(auto_remove_filter=True)]

        for provider in auto_remove_providers:
            try:
                timeout_sec = timedelta(seconds=30).total_seconds()
                with anyio.fail_after(delay=timeout_sec):
                    async with httpx.AsyncClient(base_url=str(provider.source.root), timeout=timeout_sec) as client:
                        resp = await client.get(".well-known/agent.json")
                        resp.raise_for_status()
            except Exception as ex:
                logger.error(f"Provider {provider.id} failed to respond to ping in 30 seconds: {extract_messages(ex)}")
                with suppress(EntityNotFoundError):
                    # Provider might be already deleted by another instance of this job
                    await provider_service.delete_provider(provider_id=provider.id)
                    logger.info(f"Provider {provider.id} was automatically removed")
