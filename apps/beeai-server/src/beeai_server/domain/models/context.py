# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from uuid import UUID, uuid4

from a2a.types import Artifact, Message
from pydantic import AwareDatetime, BaseModel, Field

from beeai_server.domain.models.common import Metadata
from beeai_server.utils.utils import utc_now

type ContextHistoryItemData = Artifact | Message


class ContextHistoryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    data: ContextHistoryItemData
    created_at: AwareDatetime = Field(default_factory=utc_now)
    context_id: UUID


class Context(BaseModel):
    """A context that groups files and vector stores for LLM proxy token generation."""

    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)
    last_active_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
    metadata: Metadata | None = None
