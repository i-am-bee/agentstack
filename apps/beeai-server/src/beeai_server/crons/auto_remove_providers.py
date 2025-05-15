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
from datetime import timedelta

import anyio
import httpx

from beeai_server.application import extract_messages
from beeai_server.configuration import Configuration
from beeai_server.service_layer.services.provider import ProviderService

from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory
from beeai_server.utils.periodic import periodic
from kink import inject

logger = logging.getLogger(__name__)


@periodic(period=timedelta(seconds=5))
@inject
async def auto_remove_providers(
    configuration: Configuration, uow_f: IUnitOfWorkFactory, provider_service: ProviderService
):
    async with uow_f() as uow:
        auto_remove_providers = [provider async for provider in uow.providers.list(auto_remove_filter=True)]

    for provider in auto_remove_providers:
        try:
            timeout_sec = timedelta(seconds=30).total_seconds()
            with anyio.fail_after(delay=timeout_sec):
                client = httpx.AsyncClient(base_url=str(provider.source.root), timeout=timeout_sec)
                await client.get("ping")
        except Exception as ex:
            logger.error(f"Provider {provider.id} failed to respond to ping in 30 seconds: {extract_messages(ex)}")
            await provider_service.delete_provider(provider_id=provider.id)
            logger.info(f"Provider {provider.id} was automatically removed")
