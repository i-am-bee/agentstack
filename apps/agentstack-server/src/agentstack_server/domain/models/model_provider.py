# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from openai.types import Model as OpenAIModel
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, computed_field, model_validator

from agentstack_server.domain.models.registry import ModelProviderRegistryLocation
from agentstack_server.utils.utils import utc_now


class ModelProviderState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class ModelProviderType(StrEnum):
    ANTHROPIC = "anthropic"
    CEREBRAS = "cerebras"
    CHUTES = "chutes"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    GITHUB = "github"
    GROQ = "groq"
    WATSONX = "watsonx"
    JAN = "jan"
    MISTRAL = "mistral"
    MOONSHOT = "moonshot"
    NVIDIA = "nvidia"
    OLLAMA = "ollama"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    PERPLEXITY = "perplexity"
    TOGETHER = "together"
    VOYAGE = "voyage"
    RITS = "rits"
    OTHER = "other"


class ModelCapability(StrEnum):
    LLM = "llm"
    EMBEDDING = "embedding"


class ModelProviderInfo(BaseModel):
    capabilities: set[ModelCapability]


class Model(OpenAIModel):
    provider: ModelProviderInfo
    display_name: str | None = None
    object: Literal["model"] = "model"
    created: int = 0
    owned_by: str = "unknown"


class ModelProvider(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str | None = Field(None, description="Human-readable name for the model provider")
    description: str | None = Field(None, description="Optional description of the provider")

    type: ModelProviderType = Field(..., description="Type of model provider")
    base_url: HttpUrl = Field(..., description="Base URL for the API (unique)")
    created_at: AwareDatetime = Field(default_factory=utc_now)

    # WatsonX specific fields
    watsonx_project_id: str | None = Field(
        None,
        description="WatsonX project ID (required for watsonx providers)",
        exclude=True,
    )
    watsonx_space_id: str | None = Field(
        None,
        description="WatsonX space ID (alternative to project ID)",
        exclude=True,
    )
    registry: ModelProviderRegistryLocation | None = None
    state: ModelProviderState = Field(default=ModelProviderState.ONLINE)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_watsonx_config(self):
        """Validate that watsonx providers have either project_id or space_id."""
        if self.type == ModelProviderType.WATSONX and not (bool(self.watsonx_project_id) ^ bool(self.watsonx_space_id)):
            raise ValueError("WatsonX providers must have either watsonx_project_id or watsonx_space_id")
        return self

    @computed_field
    @property
    def capabilities(self) -> set[ModelCapability]:
        return _PROVIDER_CAPABILITIES.get(self.type, set())

    @property
    def model_provider_info(self) -> ModelProviderInfo:
        return ModelProviderInfo(capabilities=self.capabilities)

    @property
    def supports_llm(self) -> bool:
        return ModelCapability.LLM in self.capabilities

    @property
    def supports_embedding(self) -> bool:
        return ModelCapability.EMBEDDING in self.capabilities

    def get_raw_model_id(self, request_model_id: str) -> str:
        return re.sub(rf"^{self.type}:", "", request_model_id)


class ModelWithScore(BaseModel):
    model_id: str
    score: float


_PROVIDER_CAPABILITIES: dict[ModelProviderType, set[ModelCapability]] = {
    ModelProviderType.ANTHROPIC: {ModelCapability.LLM},
    ModelProviderType.CEREBRAS: {ModelCapability.LLM},
    ModelProviderType.CHUTES: {ModelCapability.LLM},
    ModelProviderType.COHERE: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.DEEPSEEK: {ModelCapability.LLM},
    ModelProviderType.GEMINI: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.GITHUB: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.GROQ: {ModelCapability.LLM},
    ModelProviderType.WATSONX: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.JAN: {ModelCapability.LLM},
    ModelProviderType.MISTRAL: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.MOONSHOT: {ModelCapability.LLM},
    ModelProviderType.NVIDIA: {ModelCapability.LLM},
    ModelProviderType.OLLAMA: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.OPENAI: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.OPENROUTER: {ModelCapability.LLM},
    ModelProviderType.PERPLEXITY: {ModelCapability.LLM},
    ModelProviderType.TOGETHER: {ModelCapability.LLM},
    ModelProviderType.VOYAGE: {ModelCapability.EMBEDDING},
    ModelProviderType.RITS: {ModelCapability.LLM, ModelCapability.EMBEDDING},
    ModelProviderType.OTHER: {ModelCapability.LLM, ModelCapability.EMBEDDING},  # Other can support both
}
