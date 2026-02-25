# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.user_feedback import UserFeedback


@runtime_checkable
class IUserFeedbackRepository(Protocol):
    async def create(self, *, user_feedback: UserFeedback) -> None: ...

    async def list(
        self,
        *,
        provider_created_by: UUID | None = None,
        provider_id: UUID | None = None,
        limit: int = 50,
        after_cursor: UUID | None = None,
    ) -> tuple[list[UserFeedback], int, bool]: ...
