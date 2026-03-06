# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, computed_field

from agentstack_server.domain.models.common import Metadata
from agentstack_server.utils.utils import utc_now

ContextHistoryItemData = dict[str, Any]


class ContextHistoryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    data: ContextHistoryItemData
    created_at: AwareDatetime = Field(default_factory=utc_now)
    context_id: UUID

    @computed_field
    @property
    def kind(self) -> Literal["message", "artifact"]:
        return "artifact" if "artifact_id" in self.data else "message"


class Context(BaseModel):
    """A context that groups files and vector stores for LLM proxy token generation."""

    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)
    last_active_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    provider_id: UUID | None = None
    metadata: Metadata | None = None


class TitleGenerationState(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
