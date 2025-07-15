# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import re
from collections.abc import AsyncGenerator, Generator
from typing import Any, Literal

import fastapi
import ibm_watsonx_ai
import ibm_watsonx_ai.foundation_models
import openai
import openai.types.chat
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, SkipValidation

from beeai_server.api.dependencies import EnvServiceDependency

router = fastapi.APIRouter()

BEEAI_PROXY_VERSION = 1


class ChatCompletionRequest(BaseModel):
    """
    Corresponds to args to OpenAI `client.chat.completions.create(...)`
    """

    messages: list[
        SkipValidation[openai.types.chat.ChatCompletionMessageParam]
    ]  # SkipValidation to avoid https://github.com/pydantic/pydantic/issues/9467
    model: str | openai.types.ChatModel
    audio: openai.types.chat.ChatCompletionAudioParam | None = None
    frequency_penalty: float | None = None
    function_call: openai.types.chat.completion_create_params.FunctionCall | None = None
    functions: list[openai.types.chat.completion_create_params.Function] | None = None
    logit_bias: dict[str, int] | None = None
    logprobs: bool | None = None
    max_completion_tokens: int | None = None
    max_tokens: int | None = None
    metadata: openai.types.Metadata | None = None
    modalities: list[Literal["text", "audio"]] | None = None
    n: int | None = None
    parallel_tool_calls: bool | None = None
    prediction: openai.types.chat.ChatCompletionPredictionContentParam | None = None
    presence_penalty: float | None = None
    reasoning_effort: openai.types.ReasoningEffort | None = None
    response_format: openai.types.chat.completion_create_params.ResponseFormat | None = None
    seed: int | None = None
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = None
    stop: str | list[str] | None = None
    store: bool | None = None
    stream: bool | None = None
    stream_options: openai.types.chat.ChatCompletionStreamOptionsParam | None = None
    temperature: float | None = None
    tool_choice: openai.types.chat.ChatCompletionToolChoiceOptionParam | None = None
    tools: list[openai.types.chat.ChatCompletionToolParam] = None
    top_logprobs: int | None = None
    top_p: float | None = None
    user: str | None = None
    web_search_options: openai.types.chat.completion_create_params.WebSearchOptions | None = None


@router.post("/chat/completions")
async def create_chat_completion(env_service: EnvServiceDependency, request: ChatCompletionRequest):
    env = await env_service.list_env()

    is_rits = re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm.com/.*$", env["LLM_API_BASE"])
    is_watsonx = re.match(r"^https://[a-z0-9.-]+\.ml\.cloud\.ibm\.com/.*?$", env["LLM_API_BASE"])

    if is_watsonx:
        model = ibm_watsonx_ai.foundation_models.ModelInference(
            model_id=env["LLM_MODEL"],
            credentials=ibm_watsonx_ai.Credentials(url=env["LLM_API_BASE"], api_key=env["LLM_API_KEY"]),
            project_id=env.get("WATSONX_PROJECT_ID"),
            space_id=env.get("WATSONX_SPACE_ID"),
            params=ibm_watsonx_ai.foundation_models.model.TextChatParameters(
                frequency_penalty=request.frequency_penalty,
                logprobs=request.logprobs,
                top_logprobs=request.top_logprobs,
                presence_penalty=request.presence_penalty,
                response_format=request.response_format,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
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
                    )
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
                model=response["model_id"],
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
            api_key=env["LLM_API_KEY"],
            base_url=env["LLM_API_BASE"],
            default_headers={"RITS_API_KEY": env["LLM_API_KEY"]} if is_rits else {},
        )
        if request.stream:
            return StreamingResponse(
                _stream_openai(
                    await client.chat.completions.create(
                        **(request.model_dump(mode="json", exclude_none=True) | {"model": env["LLM_MODEL"]})
                    )
                ),
                media_type="text/event-stream",
            )
        else:
            return (
                await client.chat.completions.create(
                    **(request.model_dump(mode="json", exclude_none=True) | {"model": env["LLM_MODEL"]})
                )
            ).model_dump(mode="json") | {"beeai_proxy_version": BEEAI_PROXY_VERSION}


def _stream_watsonx(stream: Generator) -> Generator[str, Any]:
    try:
        for chunk in stream:
            yield f"""data: {
                json.dumps(
                    openai.types.chat.ChatCompletionChunk(
                        object="chat.completion.chunk",
                        id=chunk["id"],
                        created=chunk["created"],
                        model=chunk["model_id"],
                        system_fingerprint=chunk["model_version"],
                        choices=[
                            openai.types.chat.chat_completion_chunk.Choice(
                                index=choice["index"],
                                delta=openai.types.chat.chat_completion_chunk.ChoiceDelta(
                                    role=choice["delta"]["role"],
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
                    ).model_dump(mode="json")
                    | {"beeai_proxy_version": BEEAI_PROXY_VERSION}
                )
            }\n\n"""
    except Exception as e:
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': type(e).__name__}, 'beeai_proxy_version': BEEAI_PROXY_VERSION})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def _stream_openai(stream: AsyncGenerator) -> AsyncGenerator[str, Any, None]:
    try:
        async for chunk in stream:
            yield f"data: {json.dumps(chunk.model_dump(mode='json') | {'beeai_proxy_version': BEEAI_PROXY_VERSION})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': type(e).__name__}, 'beeai_proxy_version': BEEAI_PROXY_VERSION})}\n\n"
    finally:
        yield "data: [DONE]\n\n"
