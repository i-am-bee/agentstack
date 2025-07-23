# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import a2a.types
import pydantic

import beeai_sdk.a2a_extensions


class LLMFulfillment(pydantic.BaseModel):
    identifier: str | None = None
    """
    Name of the model for identification and optimization purposes. Usually corresponds to LiteLLM identifiers.
    Should be the name of the provider slash name of the model as it appears in the API.
    Examples: openai/gpt-4o, watsonx/ibm/granite-13b-chat-v2, ollama/mistral-small:22b
    """

    api_base: str
    """
    Base URL for an OpenAI-compatible API. It should provide at least /v1/chat/completions
    """

    api_key: str
    """
    API key to attach as a `Authorization: Bearer $api_key` header.
    """

    api_model: str
    """
    Model name to use with the /v1/chat/completions API.
    """


class LLMDemand(pydantic.BaseModel):
    description: str | None = None
    """
    Short description of how the model will be used, if multiple are requested.
    Intended to be shown in the UI alongside a model picker dropdown.
    """

    suggested: tuple[str, ...] = ()
    """
    Identifiers of models recommended to be used. Usually corresponds to LiteLLM identifiers.
    Should be the name of the provider slash name of the model as it appears in the API.
    Examples: openai/gpt-4o, watsonx/ibm/granite-13b-chat-v2, ollama/mistral-small:22b
    """


class LLMServiceExtensionAgentCardParams(pydantic.BaseModel):
    llm_demands: dict[str, LLMDemand]
    """Model requests that the agent requires to be provided by the client."""


class LLMServiceExtensionMessageMetadata(pydantic.BaseModel):
    llm_fulfillments: dict[str, LLMFulfillment] = {}
    """Provided models corresponding to the model requests."""


class LLMServiceExtension(beeai_sdk.a2a_extensions.Extension[LLMServiceExtensionMessageMetadata]):
    _URI: str = "https://a2a-extensions.beeai.dev/services/llm/v1"

    def __init__(self, llm_demands: dict[str, LLMDemand]) -> None:
        self.llm_demands: dict[str, LLMDemand] = llm_demands

    @typing.override
    @classmethod
    def from_agent_card(cls, agent: a2a.types.AgentCard) -> LLMServiceExtension | None:
        try:
            return LLMServiceExtension(
                llm_demands=LLMServiceExtensionAgentCardParams.model_validate(
                    next(x for x in agent.capabilities.extensions or [] if x.uri == cls._URI).params
                ).llm_demands
            )
        except StopIteration:
            return None

    @typing.override
    def to_agent_card_extensions(self, *, required: bool) -> list[a2a.types.AgentExtension]:
        return [
            a2a.types.AgentExtension(
                uri=self._URI,
                description="Agent requests the client to provide LLMs for the agent to use.",
                params=LLMServiceExtensionAgentCardParams(llm_demands=self.llm_demands).model_dump(mode="json"),
                required=required,
            )
        ]

    @typing.override
    def parse_message_metadata(self, message: a2a.types.Message) -> LLMServiceExtensionMessageMetadata | None:
        raw_metadata = getattr(message, "metadata", {}).get(self._URI, None)
        if raw_metadata is None:
            return None
        return LLMServiceExtensionMessageMetadata.model_validate(raw_metadata)

    @typing.override
    def build_message_metadata(
        self, *, llm_fulfillments: dict[str, LLMFulfillment]
    ) -> dict[str, LLMServiceExtensionMessageMetadata]:
        return {self._URI: LLMServiceExtensionMessageMetadata(llm_fulfillments=llm_fulfillments)}
