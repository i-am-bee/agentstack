# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import timedelta

from a2a.types import Artifact, Message
from cachetools import TTLCache

from agentstack_sdk.server.dependencies import Dependency
from agentstack_sdk.server.store.context_store import ContextStore, ContextStoreInstance


class MemoryContextStoreInstance(ContextStoreInstance):
    def __init__(self, context_id: str):
        self.context_id = context_id
        self._history: list[Message | Artifact] = []

    async def load_history(self) -> AsyncIterator[Message | Artifact]:
        for message in self._history.copy():
            yield message.model_copy(deep=True)

    async def store(self, data: Message | Artifact) -> None:
        self._history.append(data.model_copy(deep=True))


class InMemoryContextStore(ContextStore):
    def __init__(self, max_contexts: int = 1000, context_ttl: timedelta = timedelta(hours=1)):
        """
        Initialize in-memory context store with TTL cache.

        Args:
            max_contexts: Maximum number of contexts to keep in memory
            ttl_seconds: Time-to-live for context instances in seconds (default: 1 hour)
        """
        self._instances: TTLCache[str, MemoryContextStoreInstance] = TTLCache(
            maxsize=max_contexts, ttl=context_ttl.total_seconds()
        )

    async def create(self, context_id: str, initialized_dependencies: list[Dependency]) -> ContextStoreInstance:
        if context_id not in self._instances:
            self._instances[context_id] = MemoryContextStoreInstance(context_id)
        return self._instances[context_id]
