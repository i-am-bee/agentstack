# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from agentstack_server.domain.models.common import PaginatedResult


class InsertUserFeedbackRequest(BaseModel):
    """Request to create a user feedback."""

    provider_id: UUID
    task_id: UUID
    context_id: UUID
    rating: int = Field(..., description="Rating thats either 1 or -1")
    message: str
    comment_tags: list[str] | None = None
    comment: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v not in [1, -1]:
            raise ValueError("Rating must be either 1 or -1")
        return v


class UserFeedbackResponse(BaseModel):
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


ListUserFeedbackResponse = PaginatedResult[UserFeedbackResponse]
