# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import janus
from a2a.server.context import ServerCallContext
from a2a.server.tasks import TaskUpdater
from a2a.types import MessageSendConfiguration, Task
from pydantic import BaseModel, PrivateAttr

from beeai_sdk.a2a.types import RunYield, RunYieldResume


class RunContext(BaseModel, arbitrary_types_allowed=True):
    configuration: MessageSendConfiguration | None = None
    task_updater: TaskUpdater
    task_id: str
    context_id: str
    current_task: Task | None = None
    related_tasks: list[Task] | None = None
    call_context: ServerCallContext | None = None

    _yield_queue: janus.Queue[RunYield] = PrivateAttr(default_factory=janus.Queue)
    _yield_resume_queue: janus.Queue[RunYieldResume] = PrivateAttr(default_factory=janus.Queue)

    def yield_sync(self, value: RunYield) -> RunYieldResume:
        self._yield_queue.sync_q.put(value)
        return self._yield_resume_queue.sync_q.get()

    async def yield_async(self, value: RunYield) -> RunYieldResume:
        await self._yield_queue.async_q.put(value)
        return await self._yield_resume_queue.async_q.get()

    def shutdown(self) -> None:
        self._yield_queue.shutdown()
        self._yield_resume_queue.shutdown()
