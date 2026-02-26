# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import UUID

from kink import inject
from procrastinate import Blueprint

from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.provider_discovery import ProviderDiscoveryService

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.PROVIDER_DISCOVERY))
@inject
async def discover_provider(provider_discovery_id: str, service: ProviderDiscoveryService):
    await service.run_discovery(discovery_id=UUID(provider_discovery_id))
