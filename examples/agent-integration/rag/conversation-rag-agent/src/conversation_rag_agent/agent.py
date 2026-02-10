# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


import json
import os
from typing import Annotated

from a2a.types import DataPart, FilePart, FileWithUri, Message, Part, TextPart
from agentstack_sdk.a2a.extensions import (
    EmbeddingServiceExtensionServer,
    EmbeddingServiceExtensionSpec,
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.platform import File, PlatformFileUrl, VectorStore
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

from .embedding.client import get_embedding_client
from .embedding.embed import embed_chunks
from .extraction import extract_file
from .text_splitting import chunk_markdown
from .vector_store.create import create_vector_store
from .vector_store.search import search_vector_store

# File formats supported by the text-extraction service (docling)
default_input_modes = [
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
    "text/markdown",  # Markdown
    "text/asciidoc",  # AsciiDoc
    "text/html",  # HTML
    "application/xhtml+xml",  # XHTML
    "text/csv",  # CSV
    "image/png",  # PNG
    "image/jpeg",  # JPEG
    "image/tiff",  # TIFF
    "image/bmp",  # BMP
    "image/webp",  # WEBP
]


server = Server()


@server.agent(
    default_input_modes=default_input_modes,
    default_output_modes=["text/plain"],
)
async def conversation_rag_agent_example(
    input: Message,
    context: RunContext,
    embedding: Annotated[EmbeddingServiceExtensionServer, EmbeddingServiceExtensionSpec.single_demand()],
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    # Create embedding client
    embedding_client, embedding_model = get_embedding_client(embedding)

    # Extract files and query from input
    files: list[File] = []
    query = ""
    for part in input.parts:
        match part.root:
            case FilePart(file=FileWithUri(uri=uri)):
                files.append(await File.get(PlatformFileUrl(uri).file_id))
            case TextPart(text=text):
                query = text
            case _:
                raise NotImplementedError(f"Unsupported part: {type(part.root)}")

    # Check if vector store exists
    vector_store = None
    async for message in context.load_history():
        match message:
            case Message(parts=[Part(root=DataPart(data=data))]):
                vector_store = await VectorStore.get(data["vector_store_id"])

    # Create vector store if it does not exist
    if not vector_store:
        vector_store = await create_vector_store(embedding_client, embedding_model)
        # store vector store id in context for future messages
        data_part = DataPart(data={"vector_store_id": vector_store.id})
        await context.store(AgentMessage(parts=[data_part]))

    # Process files, add to vector store
    for file in files:
        await extract_file(file)
        async with file.load_text_content() as loaded_file:
            chunks = chunk_markdown(loaded_file.text)
        items = await embed_chunks(file, chunks, embedding_client, embedding_model)
        await vector_store.add_documents(items=items)

    # Search vector store
    if query:
        results = await search_vector_store(vector_store, query, embedding_client, embedding_model)
        snippet = [res.model_dump() for res in results]

        # TODO: You can add LLM result processing here

        yield f"# Results:\n{json.dumps(snippet, indent=2)}"
    elif files:
        yield f"{len(files)} file(s) processed"
    else:
        yield "Nothing to do"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
