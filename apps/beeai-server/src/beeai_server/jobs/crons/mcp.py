# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from contextlib import suppress
from datetime import timedelta

import anyio
import httpx
from kink import inject
from procrastinate import Blueprint

from beeai_server.configuration import get_configuration
from beeai_server.domain.models.mcp_provider import McpProviderDeploymentState
from beeai_server.service_layer.services.mcp import McpService
from beeai_server.utils.utils import extract_messages

logger = logging.getLogger(__name__)

blueprint = Blueprint()

if get_configuration().mcp.auto_remove_enabled:

    @blueprint.periodic(cron="* * * * * */5")
    @blueprint.task(queueing_lock="auto_remove_mcp_providers", queue="cron:mcp_provider")
    @inject
    async def auto_remove_providers(timestamp: int, mcp_service: McpService):
        providers = await mcp_service.list_providers()
        for provider in providers:
            try:
                timeout_sec = timedelta(seconds=30).total_seconds()
                with anyio.fail_after(delay=timeout_sec):
                    while provider.state in {McpProviderDeploymentState.RUNNING}:
                        provider = await mcp_service.read_provider(provider_id=provider.id)
                        await anyio.sleep(1)
            except Exception as ex:
                logger.error(f"Provider {provider.id} failed to become active in 30 seconds: {extract_messages(ex)}")
                with suppress(httpx.HTTPStatusError):
                    # Provider might be already deleted by another instance of this job
                    await mcp_service.delete_provider(provider_id=provider.id)
                    logger.info(f"Provider {provider.id} was automatically removed")
