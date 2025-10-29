# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.provider_build import BuildState, ProviderBuild


@runtime_checkable
class IProviderBuildRepository(Protocol):
    async def list(
        self, *, status: BuildState | None = None, user_id: UUID | None = None
    ) -> AsyncIterator[ProviderBuild]:
        yield ...  # type: ignore

    async def list_paginated(
        self,
        *,
        limit: int = 20,
        page_token: UUID | None = None,
        order: str = "desc",
        order_by: str = "created_at",
        status: BuildState | None = None,
        user_id: UUID | None = None,
        exclude_user_id: UUID | None = None,
    ) -> PaginatedResult[ProviderBuild]: ...

    async def create(self, *, provider_build: ProviderBuild) -> None: ...
    async def update(self, *, provider_build: ProviderBuild) -> None: ...
    async def get(self, *, provider_build_id: UUID, user_id: UUID | None = None) -> ProviderBuild: ...
    async def delete(self, *, provider_build_id: UUID, user_id: UUID | None = None) -> int: ...
