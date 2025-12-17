# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol, runtime_checkable
from uuid import UUID

from agentstack_server.domain.models.user_feedback import UserFeedback


@runtime_checkable
class IUserFeedbackRepository(Protocol):
    async def create(self, *, user_feedback: UserFeedback) -> None: ...

    async def list(
        self,
        *,
        user_id: UUID,
        provider_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UserFeedback], int]: ...
