# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

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
from agentstack_server.domain.models.provider import (
    NetworkProviderLocation,
    Provider,
    ProviderState,
    SourceType,
)
from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.providers import ProviderService
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)

blueprint = Blueprint()


# TODO: Can't use DI here because it's not initialized yet
# pyrefly: ignore [bad-argument-type] -- bad typing in blueprint library
@blueprint.periodic(cron=get_configuration().kagenti.sync_period_cron)
@blueprint.task(queueing_lock="sync_kagenti_agents", queue=str(Queues.CRON_PROVIDER))
@inject
async def sync_kagenti_agents(
    timestamp: int,
    configuration: Configuration,
    provider_service: ProviderService,
    user_service: UserService,
):
    if not configuration.kagenti.enabled:
        return

    from agentstack_server.infrastructure.kagenti.client import KagentiClient

    user = await user_service.get_user_by_email("admin@beeai.dev")
    client = KagentiClient(configuration.kagenti)

    try:
        kagenti_agents = await client.list_agents()
    except Exception as ex:
        logger.error(f"Failed to fetch agents from kagenti: {ex}")
        return

    # Build desired state from kagenti agents (keyed by origin = agent URL)
    desired: dict[str, dict] = {}
    for agent in kagenti_agents:
        if not agent.get("url"):
            continue
        url = agent["url"]
        desired[url] = agent

    # Get existing kagenti-sourced providers
    existing_providers = await provider_service.list_providers()
    existing_kagenti = {p.origin: p for p in existing_providers if p.source_type == SourceType.KAGENTI}

    errors = []

    # Remove providers for agents no longer in kagenti
    for origin, provider in existing_kagenti.items():
        if origin not in desired:
            try:
                await provider_service.delete_provider(provider_id=provider.id, user=user)
                logger.info(f"Removed kagenti provider {provider.id} ({origin})")
            except Exception as ex:
                errors.append(ex)

    # Create new providers for new kagenti agents
    for url, agent in desired.items():
        if url not in existing_kagenti:
            try:
                from agentstack_server.domain.models.provider import NetworkProviderLocation

                location = NetworkProviderLocation(root=url)
                await provider_service.create_provider(
                    user=user,
                    location=location,
                    origin=url,
                    source_type=SourceType.KAGENTI,
                )
                logger.info(f"Added kagenti provider from {url}")
            except Exception as ex:
                errors.append(RuntimeError(f"Failed to add kagenti provider {url}: {ex}"))

    # Update existing providers (refresh agent card)
    for url, agent in desired.items():
        if url in existing_kagenti:
            provider = existing_kagenti[url]
            try:
                from agentstack_server.domain.models.provider import NetworkProviderLocation

                location = NetworkProviderLocation(root=url)
                agent_card = await location.load_agent_card()
                if agent_card != provider.agent_card:
                    await provider_service.patch_provider(
                        provider_id=provider.id,
                        user=user,
                        agent_card=agent_card,
                    )
                    logger.info(f"Updated kagenti provider {provider.id} agent card")
            except Exception as ex:
                # Agent might not be ready yet, skip
                logger.debug(f"Failed to update kagenti provider {url}: {ex}")

    if errors:
        raise ExceptionGroup("Exceptions occurred when syncing kagenti agents", errors)


@blueprint.periodic(cron="* * * * * */5")  # pyrefly: ignore [bad-argument-type] -- bad typing in blueprint library
@blueprint.task(queueing_lock="refresh_provider_state", queue=str(Queues.CRON_PROVIDER))
@inject
async def refresh_provider_state(
    timestamp: int,
    provider_service: ProviderService,
    user_service: UserService,
):
    """Periodically check all providers' health by fetching their agent card endpoint."""
    timeout_sec = timedelta(seconds=20).total_seconds()

    async def _check_provider(provider: Provider):
        state = ProviderState.OFFLINE
        resp_card = None
        should_update = True

        user = await user_service.get_user_by_email("admin@beeai.dev")

        try:
            assert isinstance(provider.source, NetworkProviderLocation)
            async with httpx.AsyncClient(base_url=str(provider.source.a2a_url), timeout=timeout_sec) as client:
                resp_card = AgentCard.model_validate(
                    (await client.get(AGENT_CARD_WELL_KNOWN_PATH)).raise_for_status().json()
                )

                # For self-registered providers, verify their self-registration ID matches
                provider_self_reg_ext = get_extension(provider.agent_card, SELF_REGISTRATION_EXTENSION_URI)
                resp_self_reg_ext = get_extension(resp_card, SELF_REGISTRATION_EXTENSION_URI)
                if provider_self_reg_ext is not None and resp_self_reg_ext is not None:
                    if provider_self_reg_ext.params == resp_self_reg_ext.params:
                        state = ProviderState.ONLINE
                    else:
                        should_update = False
                else:
                    state = ProviderState.ONLINE

        except HTTPError as ex:
            logger.warning(
                f"Provider {provider.id} failed to respond to ping in {int(timeout_sec)} seconds: "
                f"{extract_messages(ex)}"
            )
        except Exception as ex:
            logger.debug(f"Provider {provider.id} health check failed: {ex}")
        finally:
            card_changed = resp_card is not None and provider.agent_card != resp_card
            state_changed = state != provider.state

            if should_update and (card_changed or state_changed):
                try:
                    await provider_service.patch_provider(
                        provider_id=provider.id,
                        user=user,
                        agent_card=resp_card if card_changed else None,
                        state=state if state_changed else None,
                    )
                except Exception as ex:
                    if isinstance(ex, asyncio.CancelledError):
                        raise
                    logger.error(f"Failed to update provider {provider.id}: {extract_messages(ex)}")

    providers = await provider_service.list_providers()

    async with asyncio.TaskGroup() as tg:
        for provider in providers:
            tg.create_task(_check_provider(provider))
