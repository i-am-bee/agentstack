# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import StrEnum

import pydantic

from beeai_sdk.platform.client import PlatformClient, use_platform_client


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


class ModelWithScore(pydantic.BaseModel):
    model_id: str
    score: float


class ModelCapability(StrEnum):
    LLM = "llm"
    EMBEDDING = "embedding"


class ModelProvider(pydantic.BaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    type: ModelProviderType
    base_url: pydantic.HttpUrl
    watsonx_project_id: str | None = None
    watsonx_space_id: str | None = None
    created_at: pydantic.AwareDatetime
    capabilities: set[ModelCapability]

    @staticmethod
    async def create(
        *,
        name: str | None = None,
        description: str | None = None,
        type: ModelProviderType,
        base_url: str | pydantic.HttpUrl,
        watsonx_project_id: str | None = None,
        watsonx_space_id: str | None = None,
        api_key: str,
        client: PlatformClient | None = None,
    ) -> ModelProvider:
        async with client or use_platform_client() as client:
            return pydantic.TypeAdapter(ModelProvider).validate_python(
                (
                    await client.post(
                        url="/api/v1/model_providers",
                        json={
                            "name": name,
                            "description": description,
                            "type": type,
                            "base_url": str(base_url),
                            "watsonx_project_id": watsonx_project_id,
                            "watsonx_space_id": watsonx_space_id,
                            "api_key": api_key,
                        },
                    )
                )
                .raise_for_status()
                .json()
            )

    async def get(self: ModelProvider | str, *, client: PlatformClient | None = None) -> ModelProvider:
        model_provider_id = self if isinstance(self, str) else self.id
        async with client or use_platform_client() as client:
            result = pydantic.TypeAdapter(ModelProvider).validate_python(
                (await client.get(url=f"/api/v1/model_providers/{model_provider_id}")).raise_for_status().json()
            )
        if isinstance(self, ModelProvider):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def delete(self: ModelProvider | str, *, client: PlatformClient | None = None) -> None:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        model_provider_id = self if isinstance(self, str) else self.id
        async with client or use_platform_client() as client:
            _ = (await client.delete(f"/api/v1/model_providers/{model_provider_id}")).raise_for_status()

    @staticmethod
    async def match(
        *,
        capability: ModelCapability = ModelCapability.LLM,
        suggested_models: tuple[str, ...] | None = None,
        client: PlatformClient | None = None,
    ) -> list[ModelWithScore]:
        async with client or use_platform_client() as client:
            return pydantic.TypeAdapter(list[ModelWithScore]).validate_python(
                (
                    await client.post(
                        "/api/v1/model_providers/match",
                        json={"suggested_models": suggested_models, "capability": capability},
                    )
                )
                .raise_for_status()
                .json()["items"]
            )

    @staticmethod
    async def list(*, client: PlatformClient | None = None) -> list[ModelProvider]:
        async with client or use_platform_client() as client:
            return pydantic.TypeAdapter(list[ModelProvider]).validate_python(
                (await client.get(url="/api/v1/model_providers")).raise_for_status().json()["items"]
            )
