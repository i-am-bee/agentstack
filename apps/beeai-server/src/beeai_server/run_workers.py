# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from contextlib import asynccontextmanager

import procrastinate
from kink import inject

logger = logging.getLogger(__name__)


@asynccontextmanager
@inject
async def run_workers(app: procrastinate.App):
    worker = asyncio.create_task(
        app.run_worker_async(
            install_signal_handlers=False,
            concurrency=10,  # TODO finetune per-queue concurrency
        )
    )
    logger.info(f"Starting procrastinate workers for tasks: {app.tasks.keys()}")
    try:
        yield
    finally:
        logger.info("Stopping procrastinate workers")
        worker.cancel()
        try:
            await asyncio.wait_for(worker, timeout=10)
        except TimeoutError:
            logger.info("Procrastinate workers did not terminate gracefully")
        except asyncio.CancelledError:
            logger.info("Procrastinate workers did terminate successfully")
