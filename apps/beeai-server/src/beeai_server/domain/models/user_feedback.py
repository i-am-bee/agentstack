# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, field_validator

from beeai_server.utils.utils import utc_now


class UserFeedback(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    provider_id: UUID
    task_id: UUID
    context_id: UUID
    rating: int = Field(..., description="Rating thats either 1 or -1")
    message: str
    comment_tags: list[str] | None = None
    comment: str | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v not in [1, -1]:
            raise ValueError("Rating must be either 1 or -1")
        return v
