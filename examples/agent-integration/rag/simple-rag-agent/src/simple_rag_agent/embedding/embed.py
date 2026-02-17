# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from agentstack_sdk.platform import File, VectorStoreItem
from openai import AsyncOpenAI


async def embed_chunks(
    file: File, chunks: list[str], embedding_client: AsyncOpenAI, embedding_model: str
) -> list[VectorStoreItem]:
    vector_store_items = []
    embedding_result = await embedding_client.embeddings.create(
        input=chunks,
        model=embedding_model,
        encoding_format="float",
    )
    for i, embedding_data in enumerate(embedding_result.data):
        item = VectorStoreItem(
            document_id=file.id,
            document_type="platform_file",
            model_id=embedding_model,
            text=chunks[i],
            embedding=embedding_data.embedding,
            metadata={"chunk_index": str(i)},  # add arbitrary string metadata
        )
        vector_store_items.append(item)
    return vector_store_items
