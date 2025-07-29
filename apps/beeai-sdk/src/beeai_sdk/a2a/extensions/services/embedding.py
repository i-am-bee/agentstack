# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from types import NoneType

import pydantic

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


class EmbeddingFulfillment(pydantic.BaseModel):
    identifier: str | None = None
    """
    Name of the model for identification and optimization purposes. Usually corresponds to LiteLLM identifiers.
    Should be the name of the provider slash name of the model as it appears in the API.
    Examples: openai/text-embedding-3-small, vertex_ai/textembedding-gecko, ollama/nomic-embed-text:latest
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


class EmbeddingDemand(pydantic.BaseModel):
    description: str | None = None
    """
    Short description of how the model will be used, if multiple are requested.
    Intended to be shown in the UI alongside a model picker dropdown.
    """

    suggested: tuple[str, ...] = ()
    """
    Identifiers of models recommended to be used. Usually corresponds to LiteLLM identifiers.
    Should be the name of the provider slash name of the model as it appears in the API.
    Examples: openai/text-embedding-3-small, vertex_ai/textembedding-gecko, ollama/nomic-embed-text:latest
    """


class EmbeddingServiceExtensionParams(pydantic.BaseModel):
    embedding_demands: dict[str, EmbeddingDemand]
    """Model requests that the agent requires to be provided by the client."""


class EmbeddingServiceExtensionSpec(BaseExtensionSpec[EmbeddingServiceExtensionParams]):
    URI: str = "https://a2a-extensions.beeai.dev/services/embedding/v1"


class EmbeddingServiceExtensionMetadata(pydantic.BaseModel):
    embedding_fulfillments: dict[str, EmbeddingFulfillment] = {}
    """Provided models corresponding to the model requests."""


class EmbeddingServiceExtensionServer(
    BaseExtensionServer[EmbeddingServiceExtensionSpec, EmbeddingServiceExtensionMetadata]
): ...


class EmbeddingServiceExtensionClient(BaseExtensionClient[EmbeddingServiceExtensionSpec, NoneType]):
    def fulfillment_metadata(
        self, *, embedding_fulfillments: dict[str, EmbeddingFulfillment]
    ) -> dict[str, EmbeddingServiceExtensionMetadata]:
        return {self.spec.URI: EmbeddingServiceExtensionMetadata(embedding_fulfillments=embedding_fulfillments)}
