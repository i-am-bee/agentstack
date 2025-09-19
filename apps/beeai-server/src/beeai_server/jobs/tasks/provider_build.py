# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from kink import inject
from procrastinate import Blueprint

from beeai_server.jobs.queues import Queues
from beeai_server.service_layer.services.provider_build import ProviderBuildService

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.BUILD_PROVIDER))
@inject
async def build_provider(provider_build_id: str, provider_build_service: ProviderBuildService):
    await provider_build_service.build_provider(provider_build_id=UUID(provider_build_id))
