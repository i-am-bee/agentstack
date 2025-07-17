# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing

import pydantic


class LlmModelFeatures(pydantic.BaseModel):
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


class LlmExtensionParams(pydantic.BaseModel):
    model_requests: dict[str, LlmModelFeatures]


class ProvidedModel(pydantic.BaseModel):
    identifier: str | None = None
    """
    Name of the model for identification and optimization purposes.
    Should be the Ollama model name if available (ex. "granite3.3:8b"), or OpenRouter model id under the primary provider (ex. "openai/gpt-4o").
    (This does not necessarily mean that the model is provided by Ollama or OpenRouter, it is just used for model identification.)
    """

    features: LlmModelFeatures | None = None
    """Features that the model supports. This is useful when the agent can optionally use a feature but has a fallback."""

    api_base: str
    api_key: str
    api_model: str


class ClientMessageMetadata(pydantic.BaseModel):
    provided_models: dict[str, ProvidedModel] = {}
    """Provided models corresponding to the model requests."""


class LlmModelRequest(pydantic.BaseModel):
    description: str | None = None
    """Free-form description of how the model will be used."""

    features: LlmModelFeatures | None = None
    """Requested minimal features of the model."""

    suggested: tuple[str, ...] = ()
    """
    Model ids that should work best with this agent.
    Should be the Ollama model name if available (ex. "granite3.3:8b"), or OpenRouter model id under the primary provider (ex. "openai/gpt-4o").
    (This does not necessarily mean that the model should be provided by Ollama or OpenRouter, it is just used for model identification.)
    """
