# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from asyncio import Task
from datetime import timedelta


from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import Provider
from beeai_server.service_layer.services.provider import ProviderService
from beeai_server.utils.periodic import periodic
from kink import inject, di

logger = logging.getLogger(__name__)

preinstall_background_tasks: dict[str, Task] = {}


@periodic(period=timedelta(seconds=di[Configuration].agent_registry.sync_period_sec))
@inject
async def check_registry(configuration: Configuration, provider_service: ProviderService):
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
