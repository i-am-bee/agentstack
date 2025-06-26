# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import runtime_checkable, Protocol, AsyncIterator
from uuid import UUID

from beeai_server.domain.models.provider import Provider


@runtime_checkable
class IProviderRepository(Protocol):
    async def list(self, *, auto_remove_filter: bool | None = None) -> AsyncIterator[Provider]:
        yield ...

    async def create(self, *, provider: Provider) -> None: ...
    async def get(self, *, provider_id: UUID) -> Provider: ...
    async def delete(self, *, provider_id: UUID) -> None: ...
    async def get_last_active_at(self, *, provider_id: UUID) -> None: ...
