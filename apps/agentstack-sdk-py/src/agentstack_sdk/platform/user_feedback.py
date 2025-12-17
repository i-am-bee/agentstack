# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from uuid import UUID

import pydantic

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.platform.common import PaginatedResult
from agentstack_sdk.util.utils import filter_dict


class UserFeedback(pydantic.BaseModel):
    id: UUID
    provider_id: UUID
    task_id: UUID
    context_id: UUID
    rating: int
    message: str
    comment: str | None = None
    comment_tags: list[str] | None = None
    created_at: datetime
    agent_name: str

    @staticmethod
    async def list(
        *,
        provider_id: str | None = None,
        limit: int = 50,
        after_cursor: str | None = None,
        client: PlatformClient | None = None,
    ) -> "ListUserFeedbackResponse":
        async with client or get_platform_client() as client:
            params = filter_dict({"provider_id": provider_id, "limit": limit, "after_cursor": after_cursor})
            return pydantic.TypeAdapter(ListUserFeedbackResponse).validate_python(
                (await client.get(url="/api/v1/user_feedback", params=params)).raise_for_status().json()
            )


class ListUserFeedbackResponse(PaginatedResult[UserFeedback]):
    pass
