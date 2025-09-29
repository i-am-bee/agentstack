# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from collections.abc import AsyncIterator

import janus
from a2a.server.context import ServerCallContext
from a2a.server.tasks import TaskUpdater
from a2a.types import Artifact, Message, MessageSendConfiguration, Task
from pydantic import BaseModel, PrivateAttr

from beeai_sdk.a2a.types import RunYield, RunYieldResume
from beeai_sdk.server.store.context_store import ContextStoreInstance


class RunContext(BaseModel, arbitrary_types_allowed=True):
    configuration: MessageSendConfiguration | None = None
    task_updater: TaskUpdater
    task_id: str
    context_id: str
    current_task: Task | None = None
    related_tasks: list[Task] | None = None
    call_context: ServerCallContext | None = None

    _store: ContextStoreInstance | None = PrivateAttr(None)
    _yield_queue: janus.Queue[RunYield] = PrivateAttr(default_factory=janus.Queue)
    _yield_resume_queue: janus.Queue[RunYieldResume] = PrivateAttr(default_factory=janus.Queue)

    async def store(self, data: Message | Artifact):
        if not self._store:
            raise RuntimeError("Context store is not initialized")
        if isinstance(data, Message):
            data = data.model_copy(deep=True, update={"context_id": self.context_id, "task_id": self.task_id})
        await self._store.store(data)

    async def load_history(self) -> AsyncIterator[Message | Artifact]:
        if not self._store:
            raise RuntimeError("Context store is not initialized")
        async for message in self._store.load_history():
            yield message

    def yield_sync(self, value: RunYield) -> RunYieldResume:
        self._yield_queue.sync_q.put(value)
        return self._yield_resume_queue.sync_q.get()

    async def yield_async(self, value: RunYield) -> RunYieldResume:
        await self._yield_queue.async_q.put(value)
        return await self._yield_resume_queue.async_q.get()

    def shutdown(self) -> None:
        self._yield_queue.shutdown()
        self._yield_resume_queue.shutdown()
