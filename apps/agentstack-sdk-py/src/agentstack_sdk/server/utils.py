# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from asyncio import CancelledError
from contextlib import suppress

from a2a.server.events import QueueManager


async def cancel_task(task: asyncio.Task):
    task.cancel()
    with suppress(CancelledError):
        await task


async def close_queue(queue_manager: QueueManager, queue_name: str, immediate: bool = False):
    """Closes a queue without blocking the QueueManager

    By default, QueueManager.close() will block all QueueManager operations (creating new queues, etc)
    until all queue events are processed. This can have unexpected side effects, we avoid this by closing queue
    independently and then removing it from queue_manager
    """
    if queue := await queue_manager.get(queue_name):
        await queue.close(immediate=immediate)
        await queue_manager.close(queue_name)
