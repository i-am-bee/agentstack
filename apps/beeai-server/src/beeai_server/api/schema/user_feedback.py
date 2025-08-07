# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
