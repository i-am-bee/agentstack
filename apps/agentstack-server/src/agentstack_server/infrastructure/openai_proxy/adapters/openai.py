# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Final, override

import openai.types.chat
from httpx import AsyncClient

from agentstack_server.api.schema.openai import ChatCompletionRequest, EmbeddingsRequest
from agentstack_server.domain.models.model_provider import Model, ModelProvider
from agentstack_server.domain.repositories.openai_proxy import (
    IOpenAIChatCompletionProxyAdapter,
    IOpenAIEmbeddingProxyAdapter,
)
from agentstack_server.infrastructure.openai_proxy.adapters.utils import (
    convert_embedding_output,
    parse_openai_compatible_model,
)
from agentstack_server.utils.utils import omit


class OpenAIOpenAIProxyAdapter(IOpenAIChatCompletionProxyAdapter, IOpenAIEmbeddingProxyAdapter):
    def __init__(self, provider: ModelProvider) -> None:
        super().__init__()
        self.provider: Final[ModelProvider] = provider

    def _get_client(self, api_key: str) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=api_key, base_url=str(self.provider.base_url))

    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        client = self._get_client(api_key)
        return [
            parse_openai_compatible_model(self.provider, model.model_dump())
            async for model in (await client.models.list())
        ]

    @override
    async def create_chat_completion(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> openai.types.chat.ChatCompletion:
        client = self._get_client(api_key)
        response: openai.types.chat.ChatCompletion = await client.chat.completions.create(
            **(
                request.model_dump(mode="json", exclude_none=True)
                | {"model": self.provider.get_raw_model_id(request.model)}
            )
        )
        response.model = request.model
        return response

    @override
    async def create_chat_completion_stream(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        client = self._get_client(api_key)
        async for chunk in await client.chat.completions.create(  # pyright: ignore[reportUnknownVariableType]
            **(  # pyright: ignore[reportAny]
                request.model_dump(mode="json", exclude_none=True)
                | {"model": self.provider.get_raw_model_id(request.model)}
            )
        ):
            chunk.model = request.model
            yield chunk

    @override
    async def create_embedding(
        self,
        *,
        request: EmbeddingsRequest,
        api_key: str,
    ) -> openai.types.CreateEmbeddingResponse:
        client = self._get_client(api_key)
        result = await client.embeddings.create(
            **(
                request.model_dump(mode="json", exclude_none=True)
                | {"model": self.provider.get_raw_model_id(request.model)}
            )
        )
        return convert_embedding_output(request, result)


class RitsOpenAIProxyAdapter(OpenAIOpenAIProxyAdapter):
    @override
    def _get_client(self, api_key: str) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=api_key, base_url=str(self.provider.base_url), default_headers=({"RITS_API_KEY": api_key})
        )


class AnthropicOpenAIProxyAdapter(OpenAIOpenAIProxyAdapter):
    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.provider.base_url}/models", headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}
            )
            models = response.raise_for_status().json()["data"]
            return [
                Model(
                    id=f"{self.provider.type}:{model['id']}",
                    created=int(datetime.fromisoformat(model["created_at"]).timestamp()),
                    owned_by="Anthropic",
                    object="model",
                    display_name=model["display_name"],
                    provider=self.provider.model_provider_info,
                )
                for model in models
            ]


class GithubOpenAIProxyAdapter(OpenAIOpenAIProxyAdapter):
    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        async with AsyncClient() as client:
            model_url = f"{self.provider.base_url.scheme}://{self.provider.base_url.host}/catalog/models"
            response = await client.get(model_url, headers={"Authorization": f"Bearer {api_key}"})
            models = response.raise_for_status().json()
            return [
                Model(
                    id=f"{self.provider.type}:{model['id']}",
                    display_name=model["name"],
                    owned_by=model["publisher"],
                    provider=self.provider.model_provider_info,
                    **omit(model, {"id", "name", "publisher"}),
                )
                for model in models
            ]


class VoyageOpenAIProxyAdapter(IOpenAIEmbeddingProxyAdapter):
    def __init__(self, provider: ModelProvider) -> None:
        super().__init__()
        self.provider: Final[ModelProvider] = provider

    def _get_client(self, api_key: str) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=api_key, base_url=str(self.provider.base_url))

    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        return [
            Model(
                id=f"{self.provider.type}:{model_id}",
                created=int(datetime.now().timestamp()),
                object="model",
                owned_by="voyage",
                provider=self.provider.model_provider_info,
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

    @override
    async def create_embedding(
        self,
        *,
        request: EmbeddingsRequest,
        api_key: str,
    ) -> openai.types.CreateEmbeddingResponse:
        client = self._get_client(api_key)

        # Voyage does not support 'float' value: https://docs.voyageai.com/reference/embeddings-api
        request.encoding_format = None if request.encoding_format == "float" else request.encoding_format

        result = await client.embeddings.create(
            **(
                request.model_dump(mode="json", exclude_none=True)
                | {"model": self.provider.get_raw_model_id(request.model)}
            )
        )
        return convert_embedding_output(request, result)
