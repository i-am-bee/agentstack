# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from datetime import timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.a2a_request import A2ARequestTask


@runtime_checkable
class IA2ARequestRepository(Protocol):
    async def track_request_ids_ownership(
        self,
        user_id: UUID,
        provider_id: UUID,
        task_id: str | None = None,
        context_id: str | None = None,
        allow_task_creation: bool = False,
    ) -> None: ...

    async def get_task(self, *, task_id: str, user_id: UUID) -> A2ARequestTask: ...

    async def delete_tasks(self, *, older_than: timedelta) -> int: ...
    async def delete_contexts(self, *, older_than: timedelta) -> int: ...
