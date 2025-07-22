# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import a2a.types
import pydantic

import beeai_sdk.a2a_extensions


class LLMFeatures(pydantic.BaseModel):
    streaming: bool = False
    """Model supports streaming responses (`stream`, `stream_options`)"""

    context_length: int | None = None
    """Supported context length in tokens"""

    tool_calling: bool = False
    """Supports tool calling (`tool`, `tool_choice`)"""

    tool_choice_support: tuple[typing.Literal["required", "none", "single", "auto"], ...] = ()
    """Supported values for `tool_choice`, with `"single"` meaning a specified tool."""

    response_format: tuple[typing.Literal["text", "json_object", "json_schema"], ...] = ()
    """Supposted values for `response_format`"""

    expertise: tuple[
        typing.Literal[
            "area.programming",
            "area.summarization",
            "area.translation",
            # ...
            "language.en",
            "language.cs",
            "language.de",
            # ...
        ],
        ...,
    ] = ()
    """Indicates areas, languages, tasks etc. the model is specialized in."""


class LLMAnswer(pydantic.BaseModel):
    identifier: str | None = None
    """
    Name of the model for identification and optimization purposes.
    Should be the Ollama model name if available (ex. "granite3.3:8b"), or OpenRouter model id under the primary provider (ex. "openai/gpt-4o").
    (This does not necessarily mean that the model is provided by Ollama or OpenRouter, it is just used for model identification.)
    """

    features: LLMFeatures | None = None
    """Features that the model supports. This is useful when the agent can optionally use a feature but has a fallback."""

    api_base: str
    api_key: str
    api_model: str


class LLMAsk(pydantic.BaseModel):
    description: str | None = None
    """Free-form description of how the model will be used."""

    features: LLMFeatures | None = None
    """Requested minimal features of the model."""

    suggested: tuple[str, ...] = ()
    """
    Model identifiers that should work best with this agent.
    Should be the Ollama model name if available (ex. "granite3.3:8b"), or OpenRouter model id under the primary provider (ex. "openai/gpt-4o").
    (This does not necessarily mean that the model should be provided by Ollama or OpenRouter, it is just used for model identification.)
    """


class LLMServiceExtension(beeai_sdk.a2a_extensions.Extension):
    URI = "https://a2a-extensions.beeai.dev/services/llm"

    class Params(pydantic.BaseModel):
        llm_asks: dict[str, LLMAsk]
        """Model requests that the agent requires to be provided by the client."""

    class Metadata(pydantic.BaseModel):
        llm_answers: dict[str, LLMAnswer] = {}
        """Provided models corresponding to the model requests."""

    def __init__(self, llm_asks: dict[str, LLMAsk]) -> None:
        self.llm_asks = llm_asks

    @classmethod
    def from_agent_card(cls, agent: a2a.types.AgentCard) -> LLMServiceExtension | None:
        try:
            return LLMServiceExtension(
                llm_asks=LLMServiceExtension.Params.model_validate(
                    next(x for x in agent.capabilities.extensions or [] if x.uri == cls.URI).params
                ).llm_asks
            )
        except StopIteration:
            return None

    def to_agent_card_extension(self, *, required: bool) -> a2a.types.AgentExtension:
        return a2a.types.AgentExtension(
            uri=self.URI,
            description="Agent requests the client to provide LLMs for the agent to use.",
            params=LLMServiceExtension.Params(llm_asks=self.llm_asks).model_dump(mode="json"),
            required=required,
        )

    def read_metadata(self, message: a2a.types.Message) -> LLMServiceExtension.Metadata | None:
        raw_metadata = getattr(message, "metadata", {}).get(self.URI, None)
        if raw_metadata is None:
            return None
        return LLMServiceExtension.Metadata.model_validate(raw_metadata)
