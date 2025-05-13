# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import re
import time
import uuid
from typing import Dict, List, Literal, Optional, Union, AsyncGenerator

import fastapi
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.backend import (
    ChatModelNewTokenEvent,
    ChatModelSuccessEvent,
    ChatModelErrorEvent,
    UserMessage,
    SystemMessage,
    AssistantMessage,
)
from beeai_server.routes.dependencies import EnvServiceDependency


router = fastapi.APIRouter()


class ContentItem(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ChatCompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant", "function", "tool"] = "assistant"
    content: Union[str, List[ContentItem]] = ""

    def get_text_content(self) -> str:
        if isinstance(self.content, str):
            return self.content
        return "".join(item.text for item in self.content if item.type == "text")


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int = 0
    message: ChatCompletionMessage = ChatCompletionMessage(role="assistant", content="")
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    system_fingerprint: str = "beeai-llm-gateway"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]


class ChatCompletionStreamResponseChoice(BaseModel):
    index: int = 0
    delta: ChatCompletionMessage = ChatCompletionMessage()
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    system_fingerprint: str = "beeai-llm-gateway"
    created: int
    model: str
    choices: List[ChatCompletionStreamResponseChoice]


@router.post("/chat/completions")
async def create_chat_completion(
    env_service: EnvServiceDependency,
    request: ChatCompletionRequest,
    authorization: str = fastapi.Header("Bearer dummy"),
):
    try:
        env = await env_service.list_env()
        llm = OpenAIChatModel(
            env["LLM_MODEL"],
            settings={
                "api_key": env["LLM_API_KEY"],
                "base_url": env["LLM_API_BASE"],
                "extra_headers": {"RITS_API_KEY": env["LLM_API_KEY"]}
                if re.match(r"^https://[a-z0-9.-]+.rits.fmaas.res.ibm.com/.*$", env["LLM_API_BASE"])
                else {},
            },
        )

        messages = [
            UserMessage(msg.get_text_content())
            if msg.role == "user"
            else SystemMessage(msg.get_text_content())
            if msg.role == "system"
            else AssistantMessage(msg.get_text_content())
            for msg in request.messages
            if msg.role in ["user", "system", "assistant"]
        ]

        if request.stream:
            return StreamingResponse(stream_chat_completion(llm, messages, request), media_type="text/event-stream")

        output = await llm.create(
            messages=messages,
            temperature=request.temperature,
            maxTokens=request.max_tokens,
        )

        return ChatCompletionResponse(
            id=f"chatcmpl-{str(uuid.uuid4())}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    message=ChatCompletionMessage(content=output.get_text_content()),
                    finish_reason=output.finish_reason,
                )
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stream_chat_completion(
    llm: OpenAIChatModel,
    messages: List[Union[UserMessage, SystemMessage, AssistantMessage]],
    request: ChatCompletionRequest,
) -> AsyncGenerator[str, None]:
    try:
        completion_id = f"chatcmpl-{str(uuid.uuid4())}"

        async for event, _ in llm.create(
            messages=messages,
            stream=True,
            temperature=request.temperature,
            maxTokens=request.max_tokens,
        ):
            if isinstance(event, ChatModelNewTokenEvent):
                yield f"""data: {
                    json.dumps(
                        ChatCompletionStreamResponse(
                            id=completion_id,
                            created=int(time.time()),
                            model=request.model,
                            choices=[
                                ChatCompletionStreamResponseChoice(
                                    delta=ChatCompletionMessage(content=event.value.get_text_content())
                                )
                            ],
                        ).model_dump()
                    )
                }\n\n"""
            elif isinstance(event, ChatModelSuccessEvent):
                yield f"""data: {
                    json.dumps(
                        ChatCompletionStreamResponse(
                            id=completion_id,
                            created=int(time.time()),
                            model=request.model,
                            choices=[ChatCompletionStreamResponseChoice(finish_reason=event.value.finish_reason)],
                        ).model_dump()
                    )
                }\n\n"""
                return
            elif isinstance(event, ChatModelErrorEvent):
                raise event.error
    except Exception as e:
        yield f"data: {json.dumps(dict(error=dict(message=str(e), type=type(e).__name__)))}\n\n"
    finally:
        yield "data: [DONE]\n\n"
