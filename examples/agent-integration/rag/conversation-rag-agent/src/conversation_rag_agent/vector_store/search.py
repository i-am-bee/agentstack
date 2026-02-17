# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from agentstack_sdk.platform import VectorStore, VectorStoreSearchResult
from openai import AsyncOpenAI


async def search_vector_store(
    vector_store: VectorStore,
    query: str,
    embedding_client: AsyncOpenAI,
    embedding_model: str,
) -> list[VectorStoreSearchResult]:
    embedding_response = await embedding_client.embeddings.create(input=query, model=embedding_model)
    query_vector = embedding_response.data[0].embedding
    return await vector_store.search(query_vector=query_vector, limit=5)
