# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from agentstack_sdk.a2a.extensions import EmbeddingServiceExtensionServer
from openai import AsyncOpenAI


def get_embedding_client(
    embedding: EmbeddingServiceExtensionServer,
) -> tuple[AsyncOpenAI, str]:
    if not embedding or not embedding.data:
        raise ValueError("Embedding extension not provided")

    embedding_config = embedding.data.embedding_fulfillments.get("default")
    if not embedding_config:
        raise ValueError("Default embedding configuration not found")

    embedding_client = AsyncOpenAI(
        api_key=embedding_config.api_key.get_secret_value(), base_url=embedding_config.api_base
    )
    embedding_model = embedding_config.api_model
    return embedding_client, embedding_model
