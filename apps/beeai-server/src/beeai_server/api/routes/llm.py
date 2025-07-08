# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import re
import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Union, AsyncGenerator

import fastapi
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from fastapi.concurrency import run_in_threadpool
from beeai_server.api.dependencies import EnvServiceDependency

router = fastapi.APIRouter()


class ContentItem(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ChatCompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = "assistant"
    content: Union[str, List[ContentItem]] = ""


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


class ChatCompletionResponseChoice(BaseModel):
    index: int = 0
    message: ChatCompletionMessage = ChatCompletionMessage(role="assistant", content="")
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    system_fingerprint: str = "beeai-llm-gateway"
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]


class ChatCompletionStreamResponseChoice(BaseModel):
    index: int = 0
    delta: ChatCompletionMessage = ChatCompletionMessage()
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    system_fingerprint: str = "beeai-llm-gateway"
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamResponseChoice]


@router.post("/chat/completions")
async def create_chat_completion(env_service: EnvServiceDependency, request: ChatCompletionRequest):
    env = await env_service.list_env()

    is_rits = re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm.com/.*$", env["LLM_API_BASE"])
    is_watsonx = re.match(r"^https://[a-z0-9.-]+\.ml\.cloud\.ibm\.com.*?$", env["LLM_API_BASE"])

    messages = [
        {
            "role": msg.role,
            "content": msg.content
            if isinstance(msg.content, str)
            else "".join(item.text for item in msg.content if item.type == "text"),
        }
        for msg in request.messages
    ]

    if is_watsonx:
        model = ModelInference(
            model_id=env["LLM_MODEL"],
            credentials=Credentials(url=env["LLM_API_BASE"], api_key=env["LLM_API_KEY"]),
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
                _stream_watsonx_chat_completion(model, messages, request),
                media_type="text/event-stream",
            )
        else:
            response = await run_in_threadpool(model.chat, messages=messages)
            choice = response["choices"][0]
            message_content = choice["message"]["content"]
            return ChatCompletionResponse(
                id=response.get("id", f"chatcmpl-{uuid.uuid4()}"),
                created=response.get("created", int(time.time())),
                model=request.model,
                choices=[
                    ChatCompletionResponseChoice(
                        message=ChatCompletionMessage(role="assistant", content=message_content),
                        finish_reason=choice["finish_reason"],
                    )
                ],
            )
    else:
        client = openai.AsyncOpenAI(
            api_key=env["LLM_API_KEY"],
            base_url=env["LLM_API_BASE"],
            default_headers={"RITS_API_KEY": env["LLM_API_KEY"]} if is_rits else {},
        )
        params = {**request.model_dump(exclude_none=True), "model": env["LLM_MODEL"]}

        if request.stream:
            return StreamingResponse(
                _stream_openai_chat_completion(await client.chat.completions.create(**params)),
                media_type="text/event-stream",
            )
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
                        message=ChatCompletionMessage(
                            role=openai_choice.message.role, content=openai_choice.message.content
                        ),
                        finish_reason=openai_choice.finish_reason,
                    )
                ],
            )


def _stream_watsonx_chat_completion(model: ModelInference, messages: List[Dict], request: ChatCompletionRequest):
    completion_id = f"chatcmpl-{str(uuid.uuid4())}"
    created_time = int(time.time())
    try:
        for chunk in model.chat_stream(messages=messages):
            choice = chunk["choices"][0]
            finish_reason = choice.get("finish_reason")
            response_chunk = ChatCompletionStreamResponse(
                id=completion_id,
                created=created_time,
                model=request.model,
                choices=[
                    ChatCompletionStreamResponseChoice(
                        delta=ChatCompletionMessage(
                            role="assistant", content=choice.get("delta", {}).get("content", "")
                        ),
                        finish_reason=choice.get("finish_reason"),
                    )
                ],
            )
            yield f"data: {response_chunk.model_dump_json()}\n\n"
            if finish_reason:
                break
    except Exception as e:
        error_payload = {"error": {"message": str(e), "type": type(e).__name__}}
        yield f"data: {json.dumps(error_payload)}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def _stream_openai_chat_completion(stream: AsyncGenerator) -> AsyncGenerator[str, None]:
    try:
        async for chunk in stream:
            yield f"data: {chunk.model_dump_json()}\n\n"
    except Exception as e:
        error_payload = {"error": {"message": str(e), "type": type(e).__name__}}
        yield f"data: {json.dumps(error_payload)}\n\n"
    finally:
        yield "data: [DONE]\n\n"
