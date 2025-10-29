# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from httpx import AsyncClient
from openai.types import Model as OpenAIModel
from pydantic import AwareDatetime, BaseModel, Field, HttpUrl, computed_field, model_validator

from agentstack_server.utils.utils import utc_now


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
    def _model_provider_info(self) -> ModelProviderInfo:
        return ModelProviderInfo(capabilities=self.capabilities)

    def _parse_openai_compatible_model(self, model: dict[str, Any]) -> Model:
        return Model.model_validate(
            {**model, "id": f"{self.type}:{model['id']}", "provider": self._model_provider_info}
        )

    async def load_models(self, api_key: str) -> list[Model]:
        async with AsyncClient() as client:
            match self.type:
                case ModelProviderType.WATSONX:
                    response = await client.get(f"{self.base_url}/ml/v1/foundation_model_specs?version=2025-08-27")
                    response_models = response.raise_for_status().json()["resources"]
                    available_models = []
                    for model in response_models:
                        if not model.get("lifecycle"):  # models without lifecycle might be embedding models
                            available_models.append((model, 0))
                            continue
                        events = {e["id"]: e for e in model["lifecycle"]}
                        if "withdrawn" in events:
                            continue
                        if "available" in events:
                            created = int(datetime.fromisoformat(events["available"]["start_date"]).timestamp())
                            available_models.append((model, created))
                    return [
                        Model.model_validate(
                            {
                                **model,
                                "id": f"{self.type}:{model['model_id']}",
                                "created": created,
                                "object": "model",
                                "owned_by": model["provider"],
                                "provider": self._model_provider_info,
                            }
                        )
                        for model, created in available_models
                    ]
                case ModelProviderType.VOYAGE:
                    return [
                        Model(
                            id=f"{self.type}:{model_id}",
                            created=int(datetime.now().timestamp()),
                            object="model",
                            owned_by="voyage",
                            provider=self._model_provider_info,
                        )
                        for model_id in {
                            "voyage-3-large",
                            "voyage-3.5",
                            "voyage-3.5-lite",
                            "voyage-code-3",
                            "voyage-finance-2",
                            "voyage-law-2",
                            "voyage-code-2",
                        }
                    ]
                case ModelProviderType.ANTHROPIC:
                    response = await client.get(
                        f"{self.base_url}/models", headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}
                    )
                    models = response.raise_for_status().json()["data"]
                    return [
                        Model(
                            id=f"{self.type}:{model['id']}",
                            created=int(datetime.fromisoformat(model["created_at"]).timestamp()),
                            owned_by="Anthropic",
                            object="model",
                            display_name=model["display_name"],
                            provider=self._model_provider_info,
                        )
                        for model in models
                    ]

                case ModelProviderType.RITS:
                    response = await client.get(f"{self.base_url}/models", headers={"RITS_API_KEY": api_key})
                    models = response.raise_for_status().json()["data"]
                    return [self._parse_openai_compatible_model(model) for model in models]
                case _:
                    response = await client.get(
                        f"{self.base_url}/models", headers={"Authorization": f"Bearer {api_key}"}
                    )
                    models = response.raise_for_status().json()["data"]
                    return [self._parse_openai_compatible_model(model) for model in models]

    @property
    def supports_llm(self) -> bool:
        return ModelCapability.LLM in self.capabilities

    @property
    def supports_embedding(self) -> bool:
        return ModelCapability.EMBEDDING in self.capabilities


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
    ModelProviderType.GITHUB: {ModelCapability.LLM},
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
    ModelProviderType.RITS: {ModelCapability.LLM},
    ModelProviderType.OTHER: {ModelCapability.LLM, ModelCapability.EMBEDDING},  # Other can support both
}
