# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from asyncio import CancelledError
from contextlib import suppress


async def cancel_task(task: asyncio.Task):
    task.cancel()
    with suppress(CancelledError):
        await task
