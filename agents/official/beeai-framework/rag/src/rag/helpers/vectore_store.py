# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
from turtle import st
import uuid
import json

from asyncio import TaskGroup
from datetime import timedelta
from typing import Annotated, Any, AsyncGenerator, Literal, Protocol

from beeai_sdk.a2a.extensions import TrajectoryExtensionServer, TrajectoryExtensionSpec
from click import File
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.helpers.platform import ApiClient
from rag.helpers.trajectory import TrajectoryEvent
from rag.tools.files.model import FileChatInfo
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_delay,
    wait_fixed,
)


class FileExtractionEvent(TrajectoryEvent):
    kind: str = "file_extraction"
    file_id: str


class FileEmbeddingEvent(TrajectoryEvent):
    kind: str = "file_embedding"
    file_id: str

class CreateVectorStoreEvent(TrajectoryEvent):
    kind: str = "create_vector_store"
    vector_store_id: str | None = None


async def extract_file(client: ApiClient, file: FileChatInfo) -> None:
    file_id = file.id
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


async def chunk_and_embed(
    client: ApiClient,
    file: FileChatInfo,
    vector_store_id: str,
):
    """
    Extract text from file, chunk it using RecursiveCharacterTextSplitter,
    generate embeddings, and store in vector database.
    """
    file_id = file.id
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
    client: ApiClient,
    all_files: list[FileChatInfo],
    vector_store_id: str,
    trajectory: TrajectoryExtensionServer,
) -> AsyncGenerator[dict[str, Any], None]:
    """Extract text from files and embed them into the vector store."""
    if not all_files:
        return

    response = await client.get(f"vector_stores/{vector_store_id}/documents")
    documents = response.json()["items"]

    document_ids = {
        document["file_id"] for document in documents if "file_id" in document
    }
    to_embed = [
        file_info for file_info in all_files if file_info.id not in document_ids
    ]

    if not to_embed:
        return

    # Create event storage
    extraction_events = {}
    
    # Yield extraction start events immediately for all files
    for file in to_embed:
        extraction_start_event = FileExtractionEvent(file_id=file.id, phase='start')
        extraction_events[file.id] = {'start': extraction_start_event}
        yield extraction_start_event.metadata(trajectory)

    # Pipeline: extraction -> embedding for each file
    async def extract_and_embed_pipeline(file: FileChatInfo, event_queue: asyncio.Queue):
        # Complete extraction
        await extract_file(client, file)
        extraction_end_event = FileExtractionEvent(
            parent_id=extraction_events[file.id]['start'].id, 
            file_id=file.id, 
            phase='end'
        )
        await event_queue.put(extraction_end_event.metadata(trajectory))
        
        # Start embedding immediately after extraction
        embedding_start_event = FileEmbeddingEvent(file_id=file.id, phase='start')
        await event_queue.put(embedding_start_event.metadata(trajectory))
        
        await chunk_and_embed(client, file, vector_store_id)
        embedding_end_event = FileEmbeddingEvent(
            parent_id=embedding_start_event.id, 
            file_id=file.id, 
            phase='end'
        )
        await event_queue.put(embedding_end_event.metadata(trajectory))

    # Create event queue for real-time event dispatch
    event_queue = asyncio.Queue()
    
    async with TaskGroup() as tg:
        # Create pipelined tasks
        tasks = [
            tg.create_task(extract_and_embed_pipeline(file, event_queue)) 
            for file in to_embed
        ]
        
        # Monitor for events while tasks are running
        completed_tasks = 0
        total_tasks = len(tasks)
        
        while completed_tasks < total_tasks:
            try:
                # Wait for next event or task completion
                event_metadata = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                yield event_metadata
            except asyncio.TimeoutError:
                # Check if any tasks completed
                for task in tasks[:]:
                    if task.done():
                        tasks.remove(task)
                        completed_tasks += 1


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
