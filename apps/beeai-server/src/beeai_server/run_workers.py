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
        except asyncio.TimeoutError:
            logger.info("Procrastinate workers did not terminate gracefully")
        except asyncio.CancelledError:
            logger.info("Procrastinate workers did terminate successfully")
