# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging

from kink import inject
from procrastinate import Blueprint, JobContext, builtin_tasks

from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.a2a import A2AProxyService
from agentstack_server.service_layer.services.contexts import ContextService
from agentstack_server.service_layer.services.provider_discovery import ProviderDiscoveryService

blueprint = Blueprint()

logger = logging.getLogger(__name__)


@blueprint.periodic(cron="5 * * * *")
@blueprint.task(queueing_lock="cleanup_expired_context_resources", queue=str(Queues.CRON_CLEANUP))
@inject
async def cleanup_expired_context_resources(timestamp: int, context: ContextService) -> None:
    """Delete resources of contexts that haven't been used for several days."""
    deleted_stats = await context.expire_resources()
    logger.info(f"Deleted: {deleted_stats}")


@blueprint.periodic(cron="10 * * * *")
@blueprint.task(queueing_lock="cleanup_expired_a2a_requests", queue=str(Queues.CRON_CLEANUP))
@inject
async def cleanup_expired_a2a_tasks(timestamp: int, a2a_proxy: A2AProxyService) -> None:
    """Delete tracked request objects that haven't been used for several days."""
    deleted_stats = await a2a_proxy.expire_requests()
    logger.info(f"Deleted: {deleted_stats}")


@blueprint.periodic(cron="15 * * * *")
@blueprint.task(queueing_lock="cleanup_expired_provider_discoveries", queue=str(Queues.CRON_CLEANUP))
@inject
async def cleanup_expired_provider_discoveries(timestamp: int, service: ProviderDiscoveryService) -> None:
    """Delete provider discovery records older than 1 day."""
    deleted_count = await service.cleanup_expired_discoveries()
    logger.info(f"Deleted {deleted_count} expired provider discoveries")


@blueprint.periodic(cron="*/10 * * * *")
@blueprint.task(queueing_lock="remove_old_jobs", queue=str(Queues.CRON_CLEANUP), pass_context=True)
async def remove_old_jobs(context: JobContext, timestamp: int):
    return await builtin_tasks.remove_old_jobs(
        context,
        max_hours=1,
        remove_failed=True,
        remove_cancelled=True,
        remove_aborted=True,
    )
