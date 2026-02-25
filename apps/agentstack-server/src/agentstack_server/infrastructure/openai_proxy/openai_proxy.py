# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import override

from agentstack_server.domain.models.model_provider import Model, ModelProvider, ModelProviderType
from agentstack_server.domain.repositories.openai_proxy import (
    IOpenAIChatCompletionProxyAdapter,
    IOpenAIEmbeddingProxyAdapter,
    IOpenAIProxy,
)
from agentstack_server.infrastructure.openai_proxy.adapters.openai import (
    AnthropicOpenAIProxyAdapter,
    GithubOpenAIProxyAdapter,
    OpenAIOpenAIProxyAdapter,
    RitsOpenAIProxyAdapter,
    VoyageOpenAIProxyAdapter,
)
from agentstack_server.infrastructure.openai_proxy.adapters.watsonx import WatsonXOpenAIProxyAdapter


class CustomOpenAIProxy(IOpenAIProxy):
    @override
    async def list_models(self, *, provider: ModelProvider, api_key: str) -> list[Model]:
        if provider.supports_llm:
            return await self.get_chat_completion_proxy(provider=provider).list_models(api_key=api_key)
        else:
            return await self.get_embedding_proxy(provider=provider).list_models(api_key=api_key)

    @override
    def get_chat_completion_proxy(self, *, provider: ModelProvider) -> IOpenAIChatCompletionProxyAdapter:
        if not provider.supports_llm:
            raise ValueError("Provider does not support chat completions")
        match provider.type:
            case ModelProviderType.WATSONX:
                return WatsonXOpenAIProxyAdapter(provider)
            case ModelProviderType.RITS:
                return RitsOpenAIProxyAdapter(provider)
            case ModelProviderType.ANTHROPIC:
                return AnthropicOpenAIProxyAdapter(provider)
            case ModelProviderType.GITHUB:
                return GithubOpenAIProxyAdapter(provider)
            case _:
                return OpenAIOpenAIProxyAdapter(provider)

    @override
    def get_embedding_proxy(self, *, provider: ModelProvider) -> IOpenAIEmbeddingProxyAdapter:
        if not provider.supports_embedding:
            raise ValueError("Provider does not support embeddings")
        match provider.type:
            case ModelProviderType.WATSONX:
                return WatsonXOpenAIProxyAdapter(provider)
            case ModelProviderType.RITS:
                return RitsOpenAIProxyAdapter(provider)
            case ModelProviderType.ANTHROPIC:
                return AnthropicOpenAIProxyAdapter(provider)
            case ModelProviderType.GITHUB:
                return GithubOpenAIProxyAdapter(provider)
            case ModelProviderType.VOYAGE:
                return VoyageOpenAIProxyAdapter(provider)
            case _:
                return OpenAIOpenAIProxyAdapter(provider)
