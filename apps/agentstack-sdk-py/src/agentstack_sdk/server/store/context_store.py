# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol

from a2a.types import Artifact, Message

if TYPE_CHECKING:
    from agentstack_sdk.server.dependencies import Dependency, Depends


class ContextStoreInstance(Protocol):
    async def load_history(self) -> AsyncIterator[Message | Artifact]:
        yield ...  # type: ignore

    async def store(self, data: Message | Artifact) -> None: ...


class ContextStore(abc.ABC):
    def modify_dependencies(self, dependencies: dict[str, Depends]) -> None:
        return

    @abc.abstractmethod
    async def create(self, context_id: str, initialized_dependencies: list[Dependency]) -> ContextStoreInstance: ...
