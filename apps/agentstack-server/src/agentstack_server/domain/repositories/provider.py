# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.provider import Provider, ProviderState


@runtime_checkable
class IProviderRepository(Protocol):
    def list(
        self,
        *,
        source_type: str | None = None,
        user_id: UUID | None = None,
        exclude_user_id: UUID | None = None,
        origin: str | None = None,
    ) -> AsyncIterator[Provider]: ...

    async def create(self, *, provider: Provider) -> None: ...
    async def update(self, *, provider: Provider) -> None: ...

    async def get(self, *, provider_id: UUID, user_id: UUID | None = None) -> Provider: ...
    async def delete(self, *, provider_id: UUID, user_id: UUID | None = None) -> int: ...
    async def update_state(self, provider_id: UUID, state: ProviderState) -> None: ...
    async def update_last_accessed(self, *, provider_id: UUID) -> None: ...
