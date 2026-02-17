# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import os
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import FilePart, FileWithUri, Message, TextPart
from agentstack_sdk.a2a.extensions import (
    EmbeddingServiceExtensionServer,
    EmbeddingServiceExtensionSpec,
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.platform import File, PlatformFileUrl
from agentstack_sdk.server import Server

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


@server.agent(default_input_modes=default_input_modes, default_output_modes=["text/plain"])
async def simple_rag_agent_example(
    input: Message,
    embedding: Annotated[EmbeddingServiceExtensionServer, EmbeddingServiceExtensionSpec.single_demand()],
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
) -> AsyncGenerator[RunYield, None]:
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

    if not files or not query:
        raise ValueError("No files or query provided")

    # Create vector store
    vector_store = await create_vector_store(embedding_client, embedding_model)

    # Process files, add to vector store
    for file in files:
        await extract_file(file)
        async with file.load_text_content() as loaded_file:
            chunks = chunk_markdown(loaded_file.text)
        items = await embed_chunks(file, chunks, embedding_client, embedding_model)
        await vector_store.add_documents(items=items)

    # Search vector store
    results = await search_vector_store(vector_store, query, embedding_client, embedding_model)

    # TODO: You can add LLM result processing here

    snippet = [res.model_dump() for res in results]
    yield f"# Results:\n{json.dumps(snippet, indent=2)}"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
