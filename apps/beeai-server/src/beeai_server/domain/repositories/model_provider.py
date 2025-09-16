# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from beeai_server.domain.models.model_provider import ModelCapability, ModelProvider


@runtime_checkable
class IModelProviderRepository(Protocol):
    async def create(self, *, model_provider: ModelProvider) -> None: ...
    async def get(self, *, model_provider_id: UUID) -> ModelProvider: ...
    async def list(self, *, capability: ModelCapability | None = None) -> AsyncIterator[ModelProvider]:
        yield ...  # pyright: ignore [reportReturnType]

    async def delete(self, *, model_provider_id: UUID) -> int: ...
