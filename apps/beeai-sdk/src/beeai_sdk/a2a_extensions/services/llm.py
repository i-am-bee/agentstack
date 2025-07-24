# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pydantic

from beeai_sdk.a2a_extensions.base_extension import BaseExtension


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


class LLMServiceExtensionParams(pydantic.BaseModel):
    llm_demands: dict[str, LLMDemand]
    """Model requests that the agent requires to be provided by the client."""


class LLMServiceExtensionMetadata(pydantic.BaseModel):
    llm_fulfillments: dict[str, LLMFulfillment] = {}
    """Provided models corresponding to the model requests."""


class LLMServiceExtension(BaseExtension[LLMServiceExtensionParams, LLMServiceExtensionMetadata]):
    URI: str = "https://a2a-extensions.beeai.dev/services/llm/v1"
    Params: type[LLMServiceExtensionParams] = LLMServiceExtensionParams
    Metadata: type[LLMServiceExtensionMetadata] = LLMServiceExtensionMetadata

    def fulfillment_metadata(
        self, *, llm_fulfillments: dict[str, LLMFulfillment]
    ) -> dict[str, LLMServiceExtensionMetadata]:
        return {self.URI: LLMServiceExtensionMetadata(llm_fulfillments=llm_fulfillments)}
