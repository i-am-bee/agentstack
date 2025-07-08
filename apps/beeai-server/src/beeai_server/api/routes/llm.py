# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import re
import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Union, AsyncGenerator, Generator

import fastapi
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import openai
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from fastapi.concurrency import run_in_threadpool
from beeai_server.api.dependencies import EnvServiceDependency

router = fastapi.APIRouter()


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: FunctionCall


class ChatCompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int = 0
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    system_fingerprint: str = "beeai-llm-gateway"


class StreamFunctionCall(BaseModel):
    name: Optional[str] = None
    arguments: Optional[str] = None


class StreamToolCall(BaseModel):
    index: int
    id: Optional[str] = None
    type: Literal["function"] = "function"
    function: Optional[StreamFunctionCall] = None


class ChatCompletionStreamDelta(BaseModel):
    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    tool_calls: Optional[List[StreamToolCall]] = None


class ChatCompletionStreamResponseChoice(BaseModel):
    index: int = 0
    delta: ChatCompletionStreamDelta = Field(default_factory=ChatCompletionStreamDelta)
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamResponseChoice]
    system_fingerprint: str = "beeai-llm-gateway"


@router.post("/chat/completions")
async def create_chat_completion(env_service: EnvServiceDependency, request: ChatCompletionRequest):
    env = await env_service.list_env()
    llm_api_base = env["LLM_API_BASE"]
    llm_model = env["LLM_MODEL"]

    is_rits = re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm.com/.*$", llm_api_base)
    is_watsonx = re.match(r"^https://[a-z0-9.-]+\.ml\.cloud\.ibm\.com.*?$", llm_api_base)

    messages = [msg.model_dump(exclude_none=True) for msg in request.messages]

    if is_watsonx:
        watsonx_params = {}
        if isinstance(request.tool_choice, str):
            watsonx_params["tool_choice_option"] = request.tool_choice
        elif isinstance(request.tool_choice, dict):
            watsonx_params["tool_choice"] = request.tool_choice

        model = ModelInference(
            model_id=llm_model,
            credentials=Credentials(url=llm_api_base, api_key=env["LLM_API_KEY"]),
            project_id=env.get("WATSONX_PROJECT_ID"),
            space_id=env.get("WATSONX_SPACE_ID"),
            params={
                "temperature": request.temperature,
                "max_new_tokens": request.max_tokens,
                "top_p": request.top_p,
                "presence_penalty": request.presence_penalty,
                "frequency_penalty": request.frequency_penalty,
            },
        )

        if request.stream:
            return StreamingResponse(
                _stream_watsonx_chat_completion(model, messages, request.tools, watsonx_params, request),
                media_type="text/event-stream",
            )
        else:
            response = await run_in_threadpool(model.chat, messages=messages, tools=request.tools, **watsonx_params)
            choice = response["choices"][0]
            return ChatCompletionResponse(
                id=response.get("id", f"chatcmpl-{uuid.uuid4()}"),
                created=response.get("created", int(time.time())),
                model=request.model,
                choices=[
                    ChatCompletionResponseChoice(
                        message=ChatCompletionMessage(**choice["message"]),
                        finish_reason=choice.get("finish_reason"),
                    )
                ],
            )
    else:
        client = openai.AsyncOpenAI(
            api_key=env["LLM_API_KEY"],
            base_url=llm_api_base,
            default_headers={"RITS_API_KEY": env["LLM_API_KEY"]} if is_rits else {},
        )
        params = {**request.model_dump(exclude_none=True), "model": llm_model}

        if request.stream:
            stream = await client.chat.completions.create(**params)
            return StreamingResponse(_stream_openai_chat_completion(stream), media_type="text/event-stream")
        else:
            response = await client.chat.completions.create(**params)
            openai_choice = response.choices[0]
            return ChatCompletionResponse(
                id=response.id,
                created=response.created,
                model=response.model,
                choices=[
                    ChatCompletionResponseChoice(
                        index=openai_choice.index,
                        message=ChatCompletionMessage(**openai_choice.message.model_dump()),
                        finish_reason=openai_choice.finish_reason,
                    )
                ],
            )


def _stream_watsonx_chat_completion(
    model: ModelInference,
    messages: List[Dict],
    tools: Optional[List],
    watsonx_params: Dict,
    request: ChatCompletionRequest,
) -> Generator[str, None, None]:
    completion_id = f"chatcmpl-{str(uuid.uuid4())}"
    created_time = int(time.time())
    try:
        for chunk in model.chat_stream(messages=messages, tools=tools, **watsonx_params):
            choice = chunk["choices"][0]
            response_chunk = ChatCompletionStreamResponse(
                id=completion_id,
                created=created_time,
                model=request.model,
                choices=[
                    ChatCompletionStreamResponseChoice(
                        delta=ChatCompletionStreamDelta(**choice.get("delta", {})),
                        finish_reason=choice.get("finish_reason"),
                    )
                ],
            )
            yield f"data: {response_chunk.model_dump_json(exclude_none=True)}\n\n"
            if choice.get("finish_reason"):
                break
    except Exception as e:
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': type(e).__name__}})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def _stream_openai_chat_completion(stream: AsyncGenerator) -> AsyncGenerator[str, None]:
    try:
        async for chunk in stream:
            yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': {'message': str(e), 'type': type(e).__name__}})}\n\n"
    finally:
        yield "data: [DONE]\n\n"
