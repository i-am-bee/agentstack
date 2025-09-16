# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import base64
import json
import re
import struct
import typing
from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any

import fastapi
import ibm_watsonx_ai
import ibm_watsonx_ai.foundation_models.embeddings
import openai
import openai.pagination
import openai.types.chat
from fastapi import Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from openai.types import CreateEmbeddingResponse
from starlette.status import HTTP_400_BAD_REQUEST

from beeai_server.api.dependencies import ModelProviderServiceDependency, RequiresPermissions
from beeai_server.api.schema.openai import ChatCompletionRequest, EmbeddingsRequest, MultiformatEmbedding, OpenAIPage
from beeai_server.domain.models.model_provider import Model, ModelProvider, ModelProviderType
from beeai_server.domain.models.permissions import AuthorizedUser

router = fastapi.APIRouter()

BEEAI_PROXY_VERSION = 1


@router.post("/chat/completions")
async def create_chat_completion(
    model_provider_service: ModelProviderServiceDependency,
    request: ChatCompletionRequest,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(llm={"*"}))],
):
    provider = await model_provider_service.get_provider_by_model_id(model_id=request.model)
    model_id = re.sub(rf"^{provider.type}:", "", request.model)

    if not provider.supports_llm:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Model does not support chat completions")

    api_key = await model_provider_service.get_provider_api_key(model_provider_id=provider.id)

    if provider.type == ModelProviderType.WATSONX:
        model = ibm_watsonx_ai.foundation_models.ModelInference(
            model_id=model_id,
            credentials=ibm_watsonx_ai.Credentials(url=str(provider.base_url), api_key=api_key),
            project_id=provider.watsonx_project_id,
            space_id=provider.watsonx_space_id,
            params=ibm_watsonx_ai.foundation_models.model.TextChatParameters(
                frequency_penalty=request.frequency_penalty,
                logprobs=request.logprobs,
                top_logprobs=request.top_logprobs,
                presence_penalty=request.presence_penalty,
                response_format=request.response_format,
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

        if request.stream:
            return StreamingResponse(
                _stream_watsonx(
                    model.chat_stream(
                        messages=request.messages,
                        tools=request.tools,
                        tool_choice=request.tool_choice if isinstance(request.tool_choice, dict) else None,
                        tool_choice_option=request.tool_choice if isinstance(request.tool_choice, str) else None,
                    ),
                    request.model,
                ),
                media_type="text/event-stream",
            )
        else:
            response = await run_in_threadpool(
                model.chat,
                messages=request.messages,
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
            ).model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
    else:
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=str(provider.base_url),
            default_headers=({"RITS_API_KEY": api_key} if provider.type == ModelProviderType.RITS else {}),
        )
        if request.stream:
            return StreamingResponse(
                _stream_openai(
                    await client.chat.completions.create(
                        **(request.model_dump(mode="json", exclude_none=True) | {"model": model_id})
                    ),
                    request.model,
                ),
                media_type="text/event-stream",
            )
        else:
            return (
                (
                    await client.chat.completions.create(
                        **(request.model_dump(mode="json", exclude_none=True) | {"model": model_id})
                    )
                ).model_dump(mode="json")
                | {"model": request.model}
                | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
            )


def _stream_watsonx(stream: Generator, request_model_id: str) -> Generator[str, Any]:
    try:
        for chunk in stream:
            yield f"""data: {
                json.dumps(
                    openai.types.chat.ChatCompletionChunk(
                        object="chat.completion.chunk",
                        id=chunk["id"],
                        created=chunk["created"],
                        model=request_model_id,
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
                    ).model_dump(mode="json")
                    | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
                )
            }\n\n"""
    except Exception as e:
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': type(e).__name__}, 'beeai_proxy_version': BEEAI_PROXY_VERSION})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def _stream_openai(stream: AsyncGenerator, request_model_id: str) -> AsyncGenerator[str, Any]:
    try:
        async for chunk in stream:
            data = json.dumps(
                chunk.model_dump(mode="json")
                | {"model": request_model_id}
                | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
            )
            yield f"data: {data}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': type(e).__name__}, 'beeai_proxy_version': BEEAI_PROXY_VERSION})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


def _get_provider_model_id(request_model_id: str, provider: ModelProvider):
    return re.sub(rf"^{provider.type}:", "", request_model_id)


@router.post("/embeddings")
async def create_embedding(
    request: EmbeddingsRequest,
    model_provider_service: ModelProviderServiceDependency,
    _: typing.Annotated[AuthorizedUser, Depends(RequiresPermissions(embeddings={"*"}))],
):
    provider = await model_provider_service.get_provider_by_model_id(model_id=request.model)
    model_id = _get_provider_model_id(request.model, provider)

    if not provider.supports_embedding:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Model does not support embeddings")

    if provider.type == ModelProviderType.VOYAGE:
        # Voyage does not support 'float' value: https://docs.voyageai.com/reference/embeddings-api
        request.encoding_format = None if request.encoding_format == "float" else request.encoding_format

    api_key = await model_provider_service.get_provider_api_key(model_provider_id=provider.id)

    if provider.type == ModelProviderType.WATSONX:
        watsonx_response = await run_in_threadpool(
            ibm_watsonx_ai.foundation_models.embeddings.Embeddings(
                model_id=model_id,
                credentials=ibm_watsonx_ai.Credentials(url=str(provider.base_url), api_key=api_key),
                project_id=provider.watsonx_project_id,
                space_id=provider.watsonx_space_id,
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
                        _float_list_to_base64(result["embedding"])
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
        ).model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
    else:
        result: CreateEmbeddingResponse = await openai.AsyncOpenAI(
            api_key=api_key,
            base_url=str(provider.base_url),
            default_headers=({"RITS_API_KEY": api_key} if provider.type == ModelProviderType.RITS else {}),
        ).embeddings.create(**(request.model_dump(mode="json", exclude_none=True) | {"model": model_id}))
        # Despite the typing, OpenAI library does return str embeddings when base64 is requested
        # However, some providers, like Ollama, silently don't support base64, so we have to convert
        if request.encoding_format == "base64" and result.data and isinstance(result.data[0].embedding, list):
            result.data = [
                MultiformatEmbedding(
                    object="embedding",
                    index=embedding.index,
                    embedding=_float_list_to_base64(embedding.embedding),
                )
                for embedding in result.data
            ]
        return result.model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}


def _float_list_to_base64(embedding: list[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(embedding)}f", *embedding)).decode("utf-8")


@router.get("/models")
async def list_models(
    model_provider_service: ModelProviderServiceDependency,
    _: Annotated[AuthorizedUser, Depends(RequiresPermissions(model_providers={"read"}))],
) -> OpenAIPage[Model]:
    all_models = await model_provider_service.get_all_models()
    return OpenAIPage(data=[model for _, model in all_models.values()])
