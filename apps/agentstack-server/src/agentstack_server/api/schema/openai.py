# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing
from typing import Literal

import openai.types
import pydantic
from openai.types import ReasoningEffort
from openai.types.chat import (
    ChatCompletionAudioParam,
    ChatCompletionMessageParam,
    ChatCompletionPredictionContentParam,
    ChatCompletionStreamOptionsParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from openai.types.chat.completion_create_params import Function, FunctionCall, ResponseFormat, WebSearchOptions
from pydantic import BaseModel


class EmbeddingsRequest(pydantic.BaseModel):
    """
    Corresponds to the arguments for OpenAI `client.embeddings.create(...)`.
    """

    model: str
    input: list[str] | str
    encoding_format: typing.Literal["float", "base64"] | None = None


class MultiformatEmbedding(openai.types.Embedding):
    embedding: str | list[float]  # pyright: ignore [reportIncompatibleVariableOverride]


class ChatCompletionRequest(pydantic.BaseModel):
    """
    Corresponds to args to OpenAI `client.chat.completions.create(...)`
    """

    messages: list[
        pydantic.SkipValidation[ChatCompletionMessageParam]
    ]  # SkipValidation to avoid https://github.com/pydantic/pydantic/issues/9467
    model: str | openai.types.ChatModel
    audio: ChatCompletionAudioParam | None = None
    frequency_penalty: float | None = None
    function_call: FunctionCall | None = None
    functions: list[Function] | None = None
    logit_bias: dict[str, int] | None = None
    logprobs: bool | None = None
    max_completion_tokens: int | None = None
    max_tokens: int | None = None
    metadata: openai.types.Metadata | None = None
    modalities: list[Literal["text", "audio"]] | None = None
    n: int | None = None
    parallel_tool_calls: bool | None = None
    prediction: ChatCompletionPredictionContentParam | None = None
    presence_penalty: float | None = None
    reasoning_effort: ReasoningEffort | None = None
    response_format: ResponseFormat | None = None
    seed: int | None = None
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = None
    stop: str | list[str] | None = None
    store: bool | None = None
    stream: bool | None = None
    stream_options: ChatCompletionStreamOptionsParam | None = None
    temperature: float | None = None
    tool_choice: ChatCompletionToolChoiceOptionParam | None = None
    tools: list[ChatCompletionToolParam] | None = None
    top_logprobs: int | None = None
    top_p: float | None = None
    user: str | None = None
    web_search_options: WebSearchOptions | None = None


class OpenAIPage[T](BaseModel):
    data: list[T]
    object: Literal["list"] = "list"
