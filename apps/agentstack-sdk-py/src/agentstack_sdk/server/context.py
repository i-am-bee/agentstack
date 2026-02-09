# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Literal, overload
from uuid import UUID

import janus
from a2a.types import Artifact, Message, MessageSendConfiguration, Task
from pydantic import BaseModel, PrivateAttr

from agentstack_sdk.a2a.types import RunYield, RunYieldResume
from agentstack_sdk.platform.context import ContextHistoryItem
from agentstack_sdk.server.store.context_store import ContextStoreInstance


class RunContext(BaseModel, arbitrary_types_allowed=True):
    configuration: MessageSendConfiguration | None = None
    task_id: str
    context_id: str
    current_task: Task | None = None
    related_tasks: list[Task] | None = None

    _store: ContextStoreInstance | None = PrivateAttr(None)
    _yield_queue: janus.Queue[RunYield] = PrivateAttr(default_factory=janus.Queue)
    _yield_resume_queue: janus.Queue[RunYieldResume] = PrivateAttr(default_factory=janus.Queue)

    async def store(self, data: Message | Artifact):
        if not self._store:
            raise RuntimeError("Context store is not initialized")
        if isinstance(data, Message):
            data = data.model_copy(deep=True, update={"context_id": self.context_id, "task_id": self.task_id})
        await self._store.store(data)

    @overload
    def load_history(self, load_history_items: Literal[False] = False) -> AsyncGenerator[Message | Artifact, None]: ...

    @overload
    def load_history(self, load_history_items: Literal[True]) -> AsyncGenerator[ContextHistoryItem, None]: ...

    async def load_history(
        self, load_history_items: bool = False
    ) -> AsyncGenerator[ContextHistoryItem | Message | Artifact]:
        if not self._store:
            raise RuntimeError("Context store is not initialized")
        async for item in self._store.load_history(load_history_items=load_history_items):
            yield item

    async def delete_history_from_id(self, from_id: UUID) -> None:
        if not self._store:
            raise RuntimeError("Context store is not initialized")
        await self._store.delete_history_from_id(from_id)

    def yield_sync(self, value: RunYield) -> RunYieldResume:
        self._yield_queue.sync_q.put(value)
        return self._yield_resume_queue.sync_q.get()

    async def yield_async(self, value: RunYield) -> RunYieldResume:
        await self._yield_queue.async_q.put(value)
        return await self._yield_resume_queue.async_q.get()

    def shutdown(self) -> None:
        self._yield_queue.shutdown()
        self._yield_resume_queue.shutdown()
