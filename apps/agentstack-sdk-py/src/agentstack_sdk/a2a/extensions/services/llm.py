# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from types import NoneType
from typing import TYPE_CHECKING, Any, Self

import pydantic

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec

if TYPE_CHECKING:
    from a2a.types import Message

    from agentstack_sdk.server.context import RunContext


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


class LLMServiceExtensionSpec(BaseExtensionSpec[LLMServiceExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.dev/services/llm/v1"

    @classmethod
    def single_demand(
        cls, name: str | None = None, description: str | None = None, suggested: tuple[str, ...] = ()
    ) -> Self:
        return cls(
            params=LLMServiceExtensionParams(
                llm_demands={name or "default": LLMDemand(description=description, suggested=suggested)}
            )
        )


class LLMServiceExtensionMetadata(pydantic.BaseModel):
    llm_fulfillments: dict[str, LLMFulfillment] = {}
    """Provided models corresponding to the model requests."""


class LLMServiceExtensionServer(BaseExtensionServer[LLMServiceExtensionSpec, LLMServiceExtensionMetadata]):
    def handle_incoming_message(self, message: Message, context: RunContext):
        from agentstack_sdk.platform import get_platform_client

        super().handle_incoming_message(message, context)
        if not self.data:
            return

        for fullfilment in self.data.llm_fulfillments.values():
            platform_url = str(get_platform_client().base_url)
            fullfilment.api_base = re.sub("{platform_url}", platform_url, fullfilment.api_base)


class LLMServiceExtensionClient(BaseExtensionClient[LLMServiceExtensionSpec, NoneType]):
    def fulfillment_metadata(self, *, llm_fulfillments: dict[str, LLMFulfillment]) -> dict[str, Any]:
        return {self.spec.URI: LLMServiceExtensionMetadata(llm_fulfillments=llm_fulfillments).model_dump(mode="json")}
