# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from beeai_server.domain.models.provider import Provider


@runtime_checkable
class IProviderRepository(Protocol):
    async def list(self, *, auto_remove_filter: bool | None = None) -> AsyncIterator[Provider]:
        yield ...  # type: ignore

    async def create(self, *, provider: Provider) -> None: ...
    async def get(self, *, provider_id: UUID) -> Provider: ...
    async def delete(self, *, provider_id: UUID) -> int: ...
    async def update_last_accessed(self, *, provider_id: UUID) -> None: ...
