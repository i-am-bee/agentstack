# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from a2a.types import Artifact, Message

from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionServer, PlatformApiExtensionSpec
from agentstack_sdk.platform.context import Context, ContextHistoryItem
from agentstack_sdk.server.store.context_store import ContextStore, ContextStoreInstance


class PlatformContextStore(ContextStore):
    @property
    def required_extensions(self) -> set[str]:
        return {PlatformApiExtensionSpec.URI}

    async def create(self, context_id: str) -> ContextStoreInstance:
        return PlatformContextStoreInstance(context_id=context_id)


class PlatformContextStoreInstance(ContextStoreInstance):
    def __init__(self, context_id: str):
        self._context_id = context_id

    @asynccontextmanager
    async def client(self):
        if not (ext := PlatformApiExtensionServer.current()):
            raise RuntimeError("PlatformApiExtensionServer is not initialized")
        async with ext.use_client():
            yield

    async def load_history(
        self, load_history_items: bool = False
    ) -> AsyncIterator[ContextHistoryItem | Message | Artifact]:
        async with self.client():
            async for history_item in Context.list_all_history(self._context_id):
                if load_history_items:
                    yield history_item
                else:
                    yield history_item.data

    async def store(self, data: Message | Artifact) -> None:
        async with self.client():
            await Context.add_history_item(self._context_id, data=data)

    async def delete_history_from_id(self, from_id: UUID) -> None:
        async with self.client():
            await Context.delete_history_from_id(self._context_id, from_id=from_id)
