# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import typing
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import Final, override

import ibm_watsonx_ai.foundation_models.embeddings
import openai.types.chat
from httpx import AsyncClient

from agentstack_server.api.schema.openai import ChatCompletionRequest, EmbeddingsRequest, MultiformatEmbedding
from agentstack_server.domain.models.model_provider import Model, ModelProvider
from agentstack_server.domain.repositories.openai_proxy import (
    IOpenAIChatCompletionProxyAdapter,
    IOpenAIEmbeddingProxyAdapter,
)
from agentstack_server.infrastructure.openai_proxy.adapters.utils import float_list_to_base64, iterate_in_threadpool


class WatsonXOpenAIProxyAdapter(IOpenAIChatCompletionProxyAdapter, IOpenAIEmbeddingProxyAdapter):
    def __init__(self, provider: ModelProvider) -> None:
        super().__init__()
        self.provider: Final[ModelProvider] = provider

    def _get_watsonx_model(
        self, request: ChatCompletionRequest, api_key: str
    ) -> ibm_watsonx_ai.foundation_models.ModelInference:
        model_id = self.provider.get_raw_model_id(request.model)
        return ibm_watsonx_ai.foundation_models.ModelInference(
            model_id=model_id,
            credentials=ibm_watsonx_ai.Credentials(url=str(self.provider.base_url), api_key=api_key),
            project_id=self.provider.watsonx_project_id,
            space_id=self.provider.watsonx_space_id,
            params=ibm_watsonx_ai.foundation_models.model.TextChatParameters(
                frequency_penalty=request.frequency_penalty,
                logprobs=request.logprobs,
                top_logprobs=request.top_logprobs,
                presence_penalty=request.presence_penalty,
                response_format=request.response_format,  # pyrefly: ignore[bad-argument-type]
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                max_completion_tokens=request.max_completion_tokens,
                top_p=request.top_p,
                n=request.n,
                logit_bias=request.logit_bias,
                seed=request.seed,
                stop=[request.stop] if isinstance(request.stop, str) else request.stop,
            ),
        )

    @override
    async def list_models(self, *, api_key: str) -> list[Model]:
        async with AsyncClient() as client:
            response = await client.get(f"{self.provider.base_url}/ml/v1/foundation_model_specs?version=2025-08-27")
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
                        "id": f"{self.provider.type}:{model['model_id']}",
                        "created": created,
                        "object": "model",
                        "owned_by": model["provider"],
                        "provider": self.provider.model_provider_info,
                    }
                )
                for model, created in available_models
            ]

    @override
    async def create_chat_completion(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> openai.types.chat.ChatCompletion:
        response = await asyncio.to_thread(
            self._get_watsonx_model(request, api_key).chat,
            messages=request.messages,  # pyrefly: ignore[bad-argument-type]
            tools=request.tools,
            tool_choice=request.tool_choice if isinstance(request.tool_choice, dict) else None,
            tool_choice_option=request.tool_choice if isinstance(request.tool_choice, str) else None,
        )
        return openai.types.chat.ChatCompletion(
            id=response["id"],
            choices=[
                openai.types.chat.chat_completion.Choice(
                    finish_reason=choice["finish_reason"],
                    index=choice["index"],
                    message=openai.types.chat.ChatCompletionMessage(
                        role=choice["message"]["role"],
                        content=choice["message"].get("content"),
                        refusal=choice["message"].get("refusal"),
                        tool_calls=(
                            [
                                openai.types.chat.ChatCompletionMessageToolCall(
                                    id=tool_call["id"],
                                    type="function",
                                    function=openai.types.chat.chat_completion_message_tool_call.Function(
                                        name=tool_call["function"]["name"],
                                        arguments=tool_call["function"]["arguments"],
                                    ),
                                )
                                for tool_call in choice["message"].get("tool_calls", [])
                            ]
                            or None
                        ),
                    ),
                )
                for choice in response["choices"]
            ],
            created=response["created"],
            model=request.model,
            object="chat.completion",
            system_fingerprint=response.get("model_version"),
            usage=openai.types.CompletionUsage(
                completion_tokens=response["usage"]["completion_tokens"],
                prompt_tokens=response["usage"]["prompt_tokens"],
                total_tokens=response["usage"]["total_tokens"],
            ),
        )

    def _stream_sync(
        self, request: ChatCompletionRequest, model: ibm_watsonx_ai.foundation_models.ModelInference
    ) -> Iterator[openai.types.chat.ChatCompletionChunk]:
        for chunk in model.chat_stream(
            messages=request.messages,  # pyrefly: ignore[bad-argument-type]
            tools=request.tools,
            tool_choice=request.tool_choice if isinstance(request.tool_choice, dict) else None,
            tool_choice_option=request.tool_choice if isinstance(request.tool_choice, str) else None,
        ):
            yield openai.types.chat.ChatCompletionChunk(
                object="chat.completion.chunk",
                id=chunk["id"],
                created=chunk["created"],
                model=request.model,
                system_fingerprint=chunk["model_version"],
                choices=[
                    openai.types.chat.chat_completion_chunk.Choice(
                        index=choice["index"],
                        delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(
                            role=choice["delta"].get("role"),
                            content=choice["delta"].get("content"),
                            refusal=choice["delta"].get("refusal"),
                            tool_calls=[
                                openai.types.chat.chat_completion_chunk.ChoiceDeltaToolCall(
                                    index=tool_call["index"],
                                    type="function",
                                    function=openai.types.chat.chat_completion_chunk.ChoiceDeltaFunctionCall(
                                        name=tool_call["function"]["name"],
                                        arguments=tool_call["function"]["arguments"],
                                    ),
                                )
                                for tool_call in choice["delta"].get("tool_calls", [])
                            ]
                            or None,
                        ),
                        finish_reason=choice.get("finish_reason"),
                    )
                    for choice in chunk.get("choices", [])
                ],
                usage=(
                    openai.types.CompletionUsage(
                        completion_tokens=chunk["usage"]["completion_tokens"],
                        prompt_tokens=chunk["usage"]["prompt_tokens"],
                        total_tokens=chunk["usage"]["total_tokens"],
                    )
                    if "usage" in chunk
                    else None
                ),
            )

    @override
    async def create_chat_completion_stream(
        self,
        *,
        request: ChatCompletionRequest,
        api_key: str,
    ) -> AsyncIterator[openai.types.chat.ChatCompletionChunk]:
        model = self._get_watsonx_model(request, api_key)
        async for chunk in iterate_in_threadpool(self._stream_sync(request, model)):
            yield chunk

    @override
    async def create_embedding(
        self,
        *,
        request: EmbeddingsRequest,
        api_key: str,
    ) -> openai.types.CreateEmbeddingResponse:
        watsonx_response = await asyncio.to_thread(
            ibm_watsonx_ai.foundation_models.embeddings.Embeddings(
                model_id=self.provider.get_raw_model_id(request.model),
                credentials=ibm_watsonx_ai.Credentials(url=str(self.provider.base_url), api_key=api_key),
                project_id=self.provider.watsonx_project_id,
                space_id=self.provider.watsonx_space_id,
            ).generate,
            inputs=[request.input] if isinstance(request.input, str) else request.input,
        )
        return openai.types.CreateEmbeddingResponse(
            object="list",
            model=watsonx_response["model_id"],
            data=[
                MultiformatEmbedding(
                    object="embedding",
                    index=i,
                    embedding=(
                        float_list_to_base64(result["embedding"])
                        if request.encoding_format == "base64"
                        else typing.cast(list[float], result["embedding"])
                    ),
                )
                for i, result in enumerate(watsonx_response.get("results", []))
            ],
            usage=openai.types.create_embedding_response.Usage(
                prompt_tokens=watsonx_response.get("usage", {}).get("prompt_tokens", 0),
                total_tokens=watsonx_response.get("usage", {}).get("total_tokens", 0),
            ),
        )
