# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import logging
from datetime import timedelta

import httpx
from a2a.types import AgentCard
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from httpx import HTTPError
from kink import inject
from procrastinate import Blueprint

from agentstack_server import get_configuration
from agentstack_server.configuration import Configuration
from agentstack_server.domain.constants import SELF_REGISTRATION_EXTENSION_URI
from agentstack_server.domain.models.provider import NetworkProviderLocation, Provider, ProviderType, UnmanagedState
from agentstack_server.domain.models.registry import ProviderRegistryRecord, RegistryLocation
from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.providers import ProviderService
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)

blueprint = Blueprint()


@blueprint.periodic(cron="*/1 * * * *")
@blueprint.task(queueing_lock="scale_down_providers", queue=str(Queues.CRON_PROVIDER))
@inject
async def scale_down_providers(timestamp: int, service: ProviderService):
    await service.scale_down_providers()


# TODO: Can't use DI here because it's not initialized yet
@blueprint.periodic(cron=get_configuration().agent_registry.sync_period_cron)
@blueprint.task(queueing_lock="check_registry", queue=str(Queues.CRON_PROVIDER))
@inject
async def check_registry(
    timestamp: int,
    configuration: Configuration,
    provider_service: ProviderService,
    user_service: UserService,
):
    if not configuration.agent_registry.locations:
        return

    user = await user_service.get_user_by_email("admin@beeai.dev")

    registry_by_provider_origin: dict[str, RegistryLocation] = {}
    desired_providers: dict[str, ProviderRegistryRecord] = {}
    errors = []

    try:
        await provider_service.remove_orphaned_providers()
    except Exception as ex:
        errors.extend(ex.exceptions if isinstance(ex, ExceptionGroup) else [ex])

    for registry in configuration.agent_registry.locations.values():
        for provider_record in await registry.load():
            try:
                desired_providers[provider_record.origin] = provider_record
                registry_by_provider_origin[provider_record.origin] = registry
            except ValueError as e:
                errors.append(e)

    # TODO: two providers with the same origin managed under registry are not supported
    managed_providers = {
        provider.origin: provider for provider in await provider_service.list_providers() if provider.registry
    }

    new_providers = desired_providers.keys() - managed_providers.keys()
    old_providers = managed_providers.keys() - desired_providers.keys()
    existing_providers = managed_providers.keys() & desired_providers.keys()

    # Remove old providers - to prevent agent name collisions
    for provider_origin in old_providers:
        provider = managed_providers[provider_origin]
        try:
            await provider_service.delete_provider(provider_id=provider.id, user=user)
            logger.info(f"Removed provider {provider.source}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider.source}]: Failed to remove provider: {ex}"))

    for provider_origin in new_providers:
        provider_record = desired_providers[provider_origin]
        try:
            await provider_service.create_provider(
                user=user,
                location=provider_record.location,
                origin=provider_record.origin,
                registry=registry_by_provider_origin[provider_origin],
                auto_stop_timeout=provider_record.auto_stop_timeout,
                variables=provider_record.variables,
            )
            logger.info(f"Added provider {provider_record}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider_record}]: Failed to add provider: {ex}"))

    for provider_origin in existing_providers:
        provider_record = desired_providers[provider_origin]
        provider = managed_providers[provider_origin]
        try:
            result = await provider_service.patch_provider(
                provider_id=provider.id,
                user=user,
                location=provider_record.location,
                origin=provider_record.origin,
                auto_stop_timeout=provider_record.auto_stop_timeout,
                variables=provider_record.variables,
                allow_registry_update=True,
            )
            if managed_providers[provider_origin].source.root != result.source.root:
                logger.info(f"Updated provider {provider_record}")
        except Exception as ex:
            errors.append(RuntimeError(f"[{provider_record}]: Failed to add provider: {ex}"))

    if errors:
        raise ExceptionGroup("Exceptions occurred when reloading providers", errors)


@blueprint.periodic(cron="* * * * * */5")
@blueprint.task(queueing_lock="check_unmanaged_providers", queue=str(Queues.CRON_PROVIDER))
@inject
async def refresh_unmanaged_provider_state(timestamp: int, uow_f: IUnitOfWorkFactory):
    timeout_sec = timedelta(seconds=20).total_seconds()

    async def _check_provider(provider: Provider):
        state = UnmanagedState.OFFLINE

        try:
            assert isinstance(provider.source, NetworkProviderLocation)
            async with httpx.AsyncClient(base_url=str(provider.source.a2a_url), timeout=timeout_sec) as client:
                resp_card = AgentCard.model_validate(
                    (await client.get(AGENT_CARD_WELL_KNOWN_PATH)).raise_for_status().json()
                )
                # For self-registered provider we need to check their self-registration ID, because their URL
                # might overlap (more agents on the same URL, only one can be online)
                provider_self_reg_ext = get_extension(provider.agent_card, SELF_REGISTRATION_EXTENSION_URI)
                resp_self_reg_ext = get_extension(resp_card, SELF_REGISTRATION_EXTENSION_URI)
                if provider_self_reg_ext is not None and resp_self_reg_ext is not None:
                    if provider_self_reg_ext.params == resp_self_reg_ext.params:
                        state = UnmanagedState.ONLINE
                else:
                    state = UnmanagedState.ONLINE

        except HTTPError as ex:
            logger.warning(f"Provider {provider.id} failed to respond to ping in 30 seconds: {extract_messages(ex)}")
            state = UnmanagedState.OFFLINE
        finally:
            if state != provider.unmanaged_state:
                async with uow_f() as uow:
                    await uow.providers.update_unmanaged_state(provider_id=provider.id, state=state)
                    await uow.commit()

    async with asyncio.TaskGroup() as tg, uow_f() as uow:
        async for provider in uow.providers.list(type=ProviderType.UNMANAGED):
            tg.create_task(_check_provider(provider))
