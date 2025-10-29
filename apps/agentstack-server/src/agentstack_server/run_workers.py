# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from contextlib import asynccontextmanager

import procrastinate
from kink import inject
from procrastinate.app import WorkerOptions

from agentstack_server.jobs.queues import Queues

logger = logging.getLogger(__name__)


@asynccontextmanager
@inject
async def run_workers(app: procrastinate.App):
    worker_options: list[WorkerOptions] = [
        WorkerOptions(
            name="cron_worker",
            queues=[
                str(Queues.CRON_PROVIDER),
                str(Queues.CRON_CONNECTOR),
                str(Queues.CRON_CLEANUP),
                str(Queues.CRON_MCP_PROVIDER),
                str(Queues.TOOLKIT_DELETION),
            ],
            concurrency=10,
        ),
        WorkerOptions(
            name="generate_conversation_title_worker",
            queues=[str(Queues.GENERATE_CONVERSATION_TITLE)],
            concurrency=10,
        ),
        WorkerOptions(name="text_extraction_worker", queues=[str(Queues.TEXT_EXTRACTION)], concurrency=5),
        WorkerOptions(name="build_provider_worker", queues=[str(Queues.BUILD_PROVIDER)], concurrency=5),
    ]

    worker_tasks = []
    served_queues = set()
    for opts in worker_options:
        queue_names = set(opts.get("queues", []))
        worker_tasks.append(asyncio.create_task(app.run_worker_async(**opts)))
        served_queues.update(queue_names)
    if missing_queues := Queues.all() - served_queues:
        raise RuntimeError(f"Queues: {missing_queues} are not served by any worker")
    try:
        yield
    finally:
        logger.info("Stopping procrastinate workers")
        for worker in worker_tasks:
            worker.cancel()
        try:
            await asyncio.gather(*(asyncio.wait_for(worker, timeout=10) for worker in worker_tasks))
        except TimeoutError:
            logger.info("Procrastinate workers did not terminate gracefully")
        except asyncio.CancelledError:
            logger.info("Procrastinate workers did terminate successfully")
