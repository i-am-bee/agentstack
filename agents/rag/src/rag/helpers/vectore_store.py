# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import uuid

from asyncio import TaskGroup
from datetime import timedelta
from typing import Any, AsyncGenerator, Protocol

from openai.types import CreateEmbeddingResponse

from agentstack_sdk.a2a.extensions import TrajectoryExtensionServer
from agentstack_sdk.platform import File, VectorStore
from agentstack_sdk.platform.vector_store import VectorStoreItem
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.helpers.trajectory import TrajectoryEvent
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_delay,
    wait_fixed,
)


class FileExtractionEvent(TrajectoryEvent):
    kind: str = "file_extraction"
    file: File


class FileEmbeddingEvent(TrajectoryEvent):
    kind: str = "file_embedding"
    file: File


class CreateVectorStoreEvent(TrajectoryEvent):
    kind: str = "create_vector_store"
    vector_store_id: str | None = None


class EmbeddingFunction(Protocol):
    async def __call__(self, *, input: str | list[str]) -> CreateEmbeddingResponse: ...


async def extract_file(file: File) -> None:
    file_id = file.id
    extraction = await file.create_extraction()

    async for attempt in AsyncRetrying(
        stop=stop_after_delay(timedelta(minutes=2)),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(TimeoutError),
        reraise=True,
    ):
        with attempt:
            extraction = await file.get_extraction()
            final_status = extraction.status
            if final_status == "failed":
                raise RuntimeError(f"Extraction for file {file_id} has failed: {extraction.model_dump_json()}")
            if final_status != "completed":
                raise TimeoutError("Text extraction is not finished yet")


async def chunk_and_embed(embedding_function: EmbeddingFunction, file: File, vector_store_id: str):
    """
    Extract text from file, chunk it using RecursiveCharacterTextSplitter,
    generate embeddings, and store in vector database.
    """

    vector_store = await VectorStore.get(vector_store_id)
    model_id = vector_store.model_id

    async with file.load_text_content() as loaded_file:
        text = loaded_file.text

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

    embedding = await embedding_function(input=chunks)

    vector_items = []
    for i, (chunk, embedding_data) in enumerate(zip(chunks, embedding.data, strict=False)):
        vector_items.append(
            VectorStoreItem(
                document_id=file.id,
                document_type="platform_file",
                model_id=embedding.model,
                text=chunk,
                embedding=embedding_data.embedding,
                metadata={
                    "file_id": file.id,
                    "filename": file.filename,
                    "chunk_index": str(i),
                    "chunk_id": str(uuid.uuid4()),
                    "total_chunks": str(len(chunks)),
                    "url": str(file.url),
                },
            ),
        )

    await vector_store.add_documents(vector_items)


async def embed_all_files(
    embedding_function: EmbeddingFunction,
    all_files: list[File],
    vector_store_id: str,
    trajectory: TrajectoryExtensionServer,
) -> AsyncGenerator[dict[str, Any], None]:
    """Extract text from files and embed them into the vector store."""
    if not all_files:
        return

    documents = await VectorStore.list_documents(vector_store_id)
    document_ids = {document.file_id for document in documents if document.file_id is not None}
    to_embed = [file for file in all_files if file.id not in document_ids]

    if not to_embed:
        return

    # Create event storage
    extraction_events = {}

    # Yield extraction start events immediately for all files
    for file in to_embed:
        extraction_start_event = FileExtractionEvent(file=file, phase="start")
        extraction_events[file.id] = {"start": extraction_start_event}
        yield extraction_start_event.metadata(trajectory)

    # Pipeline: extraction -> embedding for each file
    async def extract_and_embed_pipeline(file: File, event_queue: asyncio.Queue):
        # Complete extraction
        await extract_file(file)
        extraction_end_event = FileExtractionEvent(
            parent_id=extraction_events[file.id]["start"].id,
            file=file,
            phase="end",
        )
        await event_queue.put(extraction_end_event.metadata(trajectory))

        # Start embedding immediately after extraction
        embedding_start_event = FileEmbeddingEvent(file=file, phase="start")
        await event_queue.put(embedding_start_event.metadata(trajectory))

        await chunk_and_embed(embedding_function, file, vector_store_id)
        embedding_end_event = FileEmbeddingEvent(parent_id=embedding_start_event.id, file=file, phase="end")
        await event_queue.put(embedding_end_event.metadata(trajectory))

    # Create event queue for real-time event dispatch
    event_queue = asyncio.Queue()

    async with TaskGroup() as tg:
        # Create pipelined tasks
        tasks = [tg.create_task(extract_and_embed_pipeline(file, event_queue)) for file in to_embed]

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


async def create_vector_store(embedding_function: EmbeddingFunction) -> VectorStore:
    """Create a new vector store and return its ID."""
    embedding_response = await embedding_function(input="test")
    return await VectorStore.create(
        name="rag-vector-store",
        dimension=len(embedding_response.data[0].embedding),
        model_id=embedding_response.model,
    )
