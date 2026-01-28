# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import uuid
from contextlib import suppress
from datetime import timedelta
from uuid import UUID

from a2a.types import AgentCapabilities, AgentCard, AgentExtension
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from httpx import AsyncClient
from kink import inject

from agentstack_server.configuration import Configuration
from agentstack_server.domain.constants import AGENT_DETAIL_EXTENSION_URI
from agentstack_server.domain.models.provider import DockerImageProviderLocation, Provider
from agentstack_server.domain.models.provider_discovery import DiscoveryState, ProviderDiscovery
from agentstack_server.domain.models.user import User
from agentstack_server.service_layer.deployment_manager import IProviderDeploymentManager
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory
from agentstack_server.utils.a2a import get_extension
from agentstack_server.utils.docker import DockerImageID
from agentstack_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


@inject
class ProviderDiscoveryService:
    def __init__(
        self, deployment_manager: IProviderDeploymentManager, uow: IUnitOfWorkFactory, configuration: Configuration
    ):
        self._uow = uow
        self._deployment_manager = deployment_manager
        self._config = configuration

    async def create_discovery(self, *, docker_image: str, user: User) -> ProviderDiscovery:
        from agentstack_server.jobs.tasks.provider_discovery import discover_provider as task

        discovery = ProviderDiscovery(
            status=DiscoveryState.PENDING,
            docker_image=docker_image,
            created_by=user.id,
        )
        async with self._uow() as uow:
            await uow.provider_discoveries.create(discovery=discovery)
            await task.configure(queueing_lock=str(discovery.id)).defer_async(provider_discovery_id=str(discovery.id))
            await uow.commit()
        return discovery

    async def get_discovery(self, *, discovery_id: UUID, user: User | None = None) -> ProviderDiscovery:
        async with self._uow() as uow:
            return await uow.provider_discoveries.get(discovery_id=discovery_id, user_id=user.id if user else None)

    async def run_discovery(self, *, discovery_id: UUID) -> ProviderDiscovery:
        async with self._uow() as uow:
            discovery = await uow.provider_discoveries.get(discovery_id=discovery_id)
            if discovery.status != DiscoveryState.PENDING:
                logger.warning(f"Discovery {discovery_id} is not pending, skipping")
                return discovery

            discovery.status = DiscoveryState.IN_PROGRESS
            await uow.provider_discoveries.update(discovery=discovery)
            await uow.commit()

        try:
            location = DockerImageProviderLocation(DockerImageID(discovery.docker_image))
            agent_card = await self._fetch_agent_card_from_container(location)

            async with self._uow() as uow:
                discovery.agent_card = agent_card
                discovery.status = DiscoveryState.COMPLETED
                await uow.provider_discoveries.update(discovery=discovery)
                await uow.commit()

        except Exception as e:
            logger.exception(f"Discovery {discovery_id} failed")
            async with self._uow() as uow:
                discovery.status = DiscoveryState.FAILED
                discovery.error_message = str(e)
                await uow.provider_discoveries.update(discovery=discovery)
                await uow.commit()

        return discovery

    async def expire_discoveries(self, *, max_age: timedelta | None = None) -> int:
        max_age = max_age or timedelta(days=1)
        cutoff = utc_now() - max_age
        async with self._uow() as uow:
            count = await uow.provider_discoveries.delete_older_than(older_than=cutoff)
            await uow.commit()
            return count

    async def _fetch_agent_card_from_container(self, location: DockerImageProviderLocation) -> AgentCard:
        placeholder_card = AgentCard(
            name="discovery",
            description="",
            url="",
            version="",
            capabilities=AgentCapabilities(),
            default_input_modes=["text"],
            default_output_modes=["text"],
            skills=[],
        )
        temp_provider = Provider(
            source=location,
            origin=str(location.root),
            created_by=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            agent_card=placeholder_card,
        )
        try:
            await self._deployment_manager.create_or_replace(provider=temp_provider)
            await self._deployment_manager.wait_for_startup(provider_id=temp_provider.id, timeout=timedelta(minutes=1))
            url = await self._deployment_manager.get_provider_url(provider_id=temp_provider.id)
            async with AsyncClient(base_url=str(url)) as client:
                response = await client.get(AGENT_CARD_WELL_KNOWN_PATH, timeout=10)
                response.raise_for_status()
                agent_card = AgentCard.model_validate(response.json())
                return self._inject_default_agent_detail_extension(agent_card, location)
        finally:
            with suppress(Exception):
                await self._deployment_manager.delete(provider_id=temp_provider.id)

    def _inject_default_agent_detail_extension(
        self, agent_card: AgentCard, location: DockerImageProviderLocation
    ) -> AgentCard:
        if get_extension(agent_card, AGENT_DETAIL_EXTENSION_URI):
            return agent_card

        default_extension = AgentExtension(
            uri=AGENT_DETAIL_EXTENSION_URI,
            params={
                "interaction_mode": "multi-turn",
                "container_image_url": str(location.root),
            },
        )

        extensions = list(agent_card.capabilities.extensions or [])
        extensions.append(default_extension)
        agent_card.capabilities.extensions = extensions
        return agent_card
