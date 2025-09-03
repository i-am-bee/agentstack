# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol

from a2a.server.events import Event
from a2a.types import Artifact, Message, TaskArtifactUpdateEvent, TaskStatus, TaskStatusUpdateEvent

if TYPE_CHECKING:
    from beeai_sdk.server.dependencies import Dependency, Depends


class ContextStoreInstance(Protocol):
    async def load_history(self) -> AsyncIterator[Message | Artifact]:
        yield ...  # type: ignore

    async def store(self, data: Message | Artifact) -> None: ...


class ContextStore(abc.ABC):
    def modify_dependencies(self, dependencies: dict[str, Depends]) -> None:
        return

    @abc.abstractmethod
    async def create(self, context_id: str, initialized_dependencies: list[Dependency]) -> ContextStoreInstance: ...


async def record_event(event: Event, context_store: ContextStoreInstance):
    # TODO: we strip metadata because they may contain sensitive information and auth tokens
    match event:
        case Message() as msg:
            await context_store.store(msg.model_copy(update={"metadata": None}))
        case TaskStatusUpdateEvent(status=TaskStatus(message=Message() as msg)):
            await context_store.store(msg.model_copy(update={"metadata": None}))
        case TaskArtifactUpdateEvent(artifact=artifact):
            await context_store.store(artifact.model_copy(update={"metadata": None}))
