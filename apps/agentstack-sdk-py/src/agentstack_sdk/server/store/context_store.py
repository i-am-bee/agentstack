# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from a2a.types import Artifact, Message

from agentstack_sdk.platform.context import ContextHistoryItem

__all__ = [
    "ContextStore",
    "ContextStoreInstance",
]


class ContextStoreInstance(Protocol):
    def load_history(
        self, load_history_items: bool = False
    ) -> AsyncIterator[ContextHistoryItem | Message | Artifact]: ...
    async def store(self, data: Message | Artifact) -> None: ...
    async def delete_history_from_id(self, from_id: UUID) -> None: ...


class ContextStore(abc.ABC):
    @property
    def required_extensions(self) -> set[str]:
        return set()

    @abc.abstractmethod
    async def create(self, context_id: str) -> ContextStoreInstance: ...
