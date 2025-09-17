# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator

from a2a.types import Artifact, Message

from beeai_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from beeai_sdk.platform.context import Context
from beeai_sdk.server.constants import _IMPLICIT_DEPENDENCY_PREFIX
from beeai_sdk.server.dependencies import Dependency, Depends
from beeai_sdk.server.store.context_store import ContextStore, ContextStoreInstance


class PlatformContextStore(ContextStore):
    def modify_dependencies(self, dependencies: dict[str, Depends]) -> None:
        for dependency in dependencies.values():
            if dependency.extension is None:
                continue
            if dependency.extension.spec.URI == PlatformApiExtensionSpec.URI:
                dependency.extension.spec.required = True
                break
        else:
            dependencies[f"{_IMPLICIT_DEPENDENCY_PREFIX}_{PlatformApiExtensionSpec.URI}"] = Depends(
                PlatformApiExtensionServer(PlatformApiExtensionSpec())
            )

    async def create(self, context_id: str, initialized_dependencies: list[Dependency]) -> ContextStoreInstance:
        [platform_ext] = [d for d in initialized_dependencies if isinstance(d, PlatformApiExtensionServer)]
        return PlatformContextStoreInstance(context_id=context_id, platform_extension=platform_ext)


class PlatformContextStoreInstance(ContextStoreInstance):
    def __init__(self, context_id: str, platform_extension: PlatformApiExtensionServer):
        self._context_id = context_id
        self._platform_extension = platform_extension

    async def load_history(self) -> AsyncIterator[Message | Artifact]:
        async with self._platform_extension.use_client():
            async for history_item in Context.list_all_history(self._context_id):
                yield history_item.data

    async def store(self, data: Message | Artifact) -> None:
        async with self._platform_extension.use_client():
            await Context.add_history_item(self._context_id, data=data)
