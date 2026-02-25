# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from collections.abc import Iterable

import openai.types.chat

from agentstack_server.api.constants import AGENTSTACK_PROXY_VERSION
from agentstack_server.api.schema.openai import ChatCompletionRequest
from agentstack_server.types import JsonValue
from agentstack_server.utils.utils import filter_json_recursively


def camel_case_to_snake_case(name: str) -> str:
    # Insert an underscore before any uppercase letter followed by lowercase letters
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert an underscore before any uppercase letter that follows a lowercase letter or number
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def format_openai_error(error: Exception) -> JsonValue:
    error_type = camel_case_to_snake_case(type(error).__name__.removesuffix("Error").removesuffix("Exception"))
    return {
        "error": {"message": str(error), "type": error_type},
        "agentstack_proxy_version": AGENTSTACK_PROXY_VERSION,
    }


def _serialize_to_list(obj: JsonValue) -> Iterable[JsonValue]:
    if isinstance(obj, list):
        for value in obj:
            yield from _serialize_to_list(value)
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _serialize_to_list(value)
    else:
        yield obj


def estimate_llm_cost(
    object: ChatCompletionRequest | openai.types.chat.ChatCompletionChunk | openai.types.chat.ChatCompletion,
) -> int:
    """
    Estimate cost based on serialized relevant parts of the response

    Using rule of thumb for english text: https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    1 token ≈ 4 characters

    Being a bit generous here, as we include extra formatting characters and we are not sure about the exact ratio:
    1 token ≈ 5 serialized characters
    """
    match object:
        case ChatCompletionRequest() as obj:
            serialized_obj = filter_json_recursively(
                obj.model_dump(include={"messages"}, exclude_none=True, mode="json"),
                values_to_exclude={None},
                keys_to_exclude={"id", "type"},
                exclude_empty=True,
            )
        case (
            openai.types.chat.ChatCompletionChunk(
                choices=[openai.types.chat.chat_completion_chunk.Choice(delta=obj), *_rest]
            )
            | openai.types.chat.ChatCompletion(choices=[openai.types.chat.chat_completion.Choice(message=obj), *_rest])
        ):
            serialized_obj = filter_json_recursively(
                obj.model_dump(
                    include={"content", "tool_calls", "function_call", "audio", "refusal"},
                    exclude_none=True,
                    mode="json",
                ),
                values_to_exclude={None},
                keys_to_exclude={"id", "type"},
                exclude_empty=True,
            )
        case _:
            return 0

    serialized_chars: str = ";".join(str(v) for v in _serialize_to_list(serialized_obj))
    if 0 < len(serialized_chars) < 20:
        return 1  # probably a single token
    return len(serialized_chars) // 5
