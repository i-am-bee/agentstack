# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from agentstack_server.domain.models.connector import Connector


class IConnectorRepository(Protocol):
    async def list(self, *, user_id: UUID | None = None) -> AsyncIterator[Connector]:
        yield ...  # type: ignore

    async def create(self, *, connector: Connector) -> None: ...
    async def update(self, *, connector: Connector) -> None: ...
    async def get(self, *, connector_id: UUID, user_id: UUID | None = None) -> Connector: ...
    async def get_by_auth(self, *, auth_state: str) -> Connector: ...
    async def delete(self, *, connector_id: UUID, user_id: UUID | None = None) -> int: ...
