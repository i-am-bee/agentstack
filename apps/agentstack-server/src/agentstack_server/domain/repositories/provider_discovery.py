# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.provider_discovery import DiscoveryState, ProviderDiscovery


@runtime_checkable
class IProviderDiscoveryRepository(Protocol):
    async def create(self, *, discovery: ProviderDiscovery) -> None: ...
    async def get(self, *, discovery_id: UUID, user_id: UUID | None = None) -> ProviderDiscovery: ...
    async def update(self, *, discovery: ProviderDiscovery) -> None: ...
    async def delete(self, *, discovery_id: UUID, user_id: UUID | None = None) -> int: ...
    async def delete_older_than(self, *, older_than: datetime) -> int: ...

    def list(
        self, *, user_id: UUID | None = None, status: DiscoveryState | None = None
    ) -> AsyncIterator[ProviderDiscovery]: ...
