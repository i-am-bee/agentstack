# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.model_provider import ModelCapability, ModelProvider, ModelProviderState


@runtime_checkable
class IModelProviderRepository(Protocol):
    async def create(self, *, model_provider: ModelProvider) -> None: ...
    async def get(self, *, model_provider_id: UUID) -> ModelProvider: ...
    def list(self, *, capability: ModelCapability | None = None) -> AsyncIterator[ModelProvider]: ...
    async def update(self, *, model_provider: ModelProvider) -> None: ...
    async def update_state(self, *, model_provider_id: UUID, state: ModelProviderState) -> None: ...
    async def delete(self, *, model_provider_id: UUID) -> int: ...
