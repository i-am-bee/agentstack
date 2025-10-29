# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field

from agentstack_server.utils.utils import utc_now


class SystemConfiguration(BaseModel):
    """Global system configuration that can be updated by administrators."""

    id: UUID = Field(default_factory=uuid4)

    default_llm_model: str | None = Field(default=None, description="Default LLM model (e.g., 'openai:gpt-4o')")
    default_embedding_model: str | None = Field(
        default=None, description="Default embedding model (e.g., 'openai:text-embedding-3-small')"
    )

    updated_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID

    @property
    def has_defaults_configured(self) -> bool:
        return bool(self.default_llm_model and self.default_embedding_model)
