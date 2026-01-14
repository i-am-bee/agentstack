# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from a2a.types import Artifact, Message

from agentstack_sdk.platform.context import ContextHistoryItem

if TYPE_CHECKING:
    from agentstack_sdk.server.dependencies import Dependency, Depends


class ContextStoreInstance(Protocol):
    async def load_history(
        self, load_history_items: bool = False
    ) -> AsyncIterator[ContextHistoryItem | Message | Artifact]:
        yield ...  # type: ignore

    async def store(self, data: Message | Artifact) -> None: ...

    async def delete_history_from_id(self, from_id: UUID) -> None: ...


class ContextStore(abc.ABC):
    def modify_dependencies(self, dependencies: dict[str, Depends]) -> None:
        return

    @abc.abstractmethod
    async def create(self, context_id: str, initialized_dependencies: list[Dependency]) -> ContextStoreInstance: ...
