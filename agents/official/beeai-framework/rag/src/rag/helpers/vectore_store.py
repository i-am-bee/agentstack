# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from asyncio import TaskGroup
from datetime import timedelta
import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from litellm.llms.azure_ai import embed
from pydantic import AnyUrl
from rag.helpers.platform import ApiClient, FileInfo
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_delay,
    wait_fixed,
)


async def extract_file(client: ApiClient, file_id: str) -> None:
    await client.post(f"files/{file_id}/extraction")

    async for attempt in AsyncRetrying(
        stop=stop_after_delay(timedelta(minutes=2)),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(TimeoutError),
        reraise=True,
    ):
        with attempt:
            response = await client.get(f"files/{file_id}/extraction")
            extraction_data = response.json()
            final_status = extraction_data["status"]
            if final_status == "failed":
                raise RuntimeError(
                    f"Extraction for file {file_id} has failed: {extraction_data}"
                )
            if final_status != "completed":
                raise TimeoutError("Text extraction is not finished yet")


async def chunk_and_embed(client: ApiClient, file_id: str, vector_store_id: str):
    """
    Extract text from file, chunk it using RecursiveCharacterTextSplitter,
    generate embeddings, and store in vector database.
    """
    response = await client.get(f"files/{file_id}/text_content")
    text = response.text

    if not text.strip():
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_text(text)

    if not chunks:
        return

    embed_response = await client.post(
        "llm/embeddings", json={"model": "text-embedding-model", "input": chunks}
    )
    embeddings_data = embed_response.json()

    vector_items = []
    for i, (chunk, embedding_data) in enumerate(
        zip(chunks, embeddings_data["data"], strict=False)
    ):
        vector_items.append(
            {
                "document_id": file_id,
                "document_type": "platform_file",
                "model_id": "text-embedding-model",
                "text": chunk,
                "embedding": embedding_data["embedding"],
                "metadata": {
                    "file_id": file_id,
                    "chunk_index": str(i),
                    "chunk_id": str(uuid.uuid4()),
                    "total_chunks": str(len(chunks)),
                },
            }
        )

    upload_response = await client.put(
        f"vector_stores/{vector_store_id}", json=vector_items
    )


async def embed_all_files(
    client: ApiClient, all_files: set[AnyUrl | None], vector_store_id: str
):
    """Extract text from files and embed them into the vector store."""
    if not all_files:
        return

    response = await client.get(f"vector_stores/{vector_store_id}/documents")
    documents = response.json()["items"]

    file_ids = {re.search(r"/([^/]+)/content", str(url)) for url in all_files}
    file_ids = {match.group(1) for match in file_ids if match}
    document_ids = {
        document["file_id"] for document in documents if "file_id" in document
    }
    to_embed = {file_id for file_id in file_ids if file_id not in document_ids}

    if not to_embed:
        return

    async with TaskGroup() as tg:
        for file_id in to_embed:
            tg.create_task(extract_file(client, file_id))

    async with TaskGroup() as tg:
        for file_id in to_embed:
            tg.create_task(chunk_and_embed(client, file_id, vector_store_id))


async def create_vector_store(client: ApiClient) -> str:
    """Create a new vector store and return its ID."""

    response = await client.post(
        "llm/embeddings", json={"model": "text-embedding-model", "input": "dummy"}
    )
    response_data = response.json()
    dimension = len(response_data["data"][0]["embedding"])

    response = await client.post(
        "vector_stores",
        json={
            "name": "rag-vector-store",
            "dimension": dimension,
            "model_id": "text-embedding-model",
        },
    )
    vector_store_data = response.json()
    return vector_store_data["id"]
