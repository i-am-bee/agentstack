# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Final, Protocol

from a2a.server.events import Event
from a2a.types import Artifact, Message, TaskArtifactUpdateEvent, TaskStatus, TaskStatusUpdateEvent

from beeai_sdk.a2a.extensions.services.embedding import EmbeddingServiceExtensionSpec
from beeai_sdk.a2a.extensions.services.llm import LLMServiceExtensionSpec
from beeai_sdk.a2a.extensions.services.platform import PlatformApiExtensionSpec

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


FORBIDDEN_METADATA_EXTENSION_URIS: Final = {
    PlatformApiExtensionSpec.URI,
    LLMServiceExtensionSpec.URI,
    EmbeddingServiceExtensionSpec.URI,
}


def filter_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return metadata
    return {k: v for k, v in metadata.items() if k not in FORBIDDEN_METADATA_EXTENSION_URIS}


async def record_event(event: Event, context_store: ContextStoreInstance):
    # TODO: we filter metadata because they may contain sensitive information and auth tokens
    match event:
        case Message() as msg:
            await context_store.store(msg.model_copy(update={"metadata": filter_metadata(msg.metadata)}))
        case TaskStatusUpdateEvent(status=TaskStatus(message=Message() as msg)):
            await context_store.store(msg.model_copy(update={"metadata": filter_metadata(msg.metadata)}))
        case TaskArtifactUpdateEvent(artifact=artifact):
            await context_store.store(artifact.model_copy(update={"metadata": filter_metadata(artifact.metadata)}))
