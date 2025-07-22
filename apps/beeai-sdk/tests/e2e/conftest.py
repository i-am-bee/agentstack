# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, closing

import httpx
import pytest
from a2a.client import A2AClient, create_text_message_object
from a2a.types import Artifact, DataPart, FilePart, FileWithBytes, Message, Part, TaskState, TaskStatus, TextPart
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from beeai_sdk.server import Server
from beeai_sdk.server.context import Context
from beeai_sdk.server.types import ArtifactChunk, RunYield, RunYieldResume


def get_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))  # Bind to any available port
        return int(sock.getsockname()[1])


@asynccontextmanager
async def run_server(server: Server, port: int) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(asyncio.to_thread(server.run, self_registration=False, port=port))

        try:
            async with httpx.AsyncClient(timeout=None) as httpx_client:
                async for attempt in AsyncRetrying(stop=stop_after_attempt(10), wait=wait_fixed(0.1), reraise=True):
                    with attempt:
                        if not server.server or not server.server.started:
                            raise ConnectionError("Server hasn't started yet")
                        base_url = f"http://localhost:{port}"
                        client = await A2AClient.get_client_from_agent_card_url(
                            httpx_client=httpx_client, base_url=base_url
                        )
                        yield server, client
        finally:
            server.should_exit = True


@pytest.fixture
def create_server_with_agent():
    """Factory fixture that creates a server with the given agent function."""

    @asynccontextmanager
    async def _create_server(agent_fn):
        server = Server()
        server.agent()(agent_fn)
        async with run_server(server, get_free_port()) as (server, client):
            yield server, client

    return _create_server


@pytest.fixture
async def echo(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def echo(message: Message, context: Context) -> AsyncGenerator[str, Message]:
        for part in message.parts:
            if hasattr(part.root, "text"):
                yield part.root.text

    async with create_server_with_agent(echo) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def slow_echo(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def slow_echo(message: Message, context: Context) -> AsyncGenerator[str, Message]:
        # Slower version with delay
        for part in message.parts:
            if hasattr(part.root, "text"):
                await asyncio.sleep(1)
                yield part.root.text

    async with create_server_with_agent(slow_echo) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def awaiter(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def awaiter(message: Message, context: Context) -> AsyncGenerator[TaskStatus | str, Message]:
        # Agent that requires input
        yield "Processing initial message..."
        resume_message = yield TaskStatus(
            state=TaskState.input_required,
            message=create_text_message_object(content="Please provide additional input"),
        )
        yield f"Received resume: {resume_message.parts[0].root.text if resume_message.parts else 'empty'}"

    async with create_server_with_agent(awaiter) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def failer(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def failer(message: Message, context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
        # Agent that raises an error
        yield ValueError("Wrong question buddy!")

    async with create_server_with_agent(failer) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def raiser(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def raiser(message: Message, context: Context) -> AsyncGenerator[str, Message]:
        # Another failing agent
        raise RuntimeError("Wrong question buddy!")

    async with create_server_with_agent(raiser) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def artifact_producer(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def artifact_producer(message: Message, context: Context) -> AsyncGenerator[str | Artifact, Message]:
        # Agent producing artifacts
        yield "Processing with artifacts"

        # Create artifacts with proper parts structure
        yield Artifact(
            artifact_id=str(1),
            name="text-result.txt",
            parts=[Part(root=TextPart(text="This is a text artifact result"))],
        )

        yield Artifact(
            artifact_id=str(2),
            name="data.json",
            parts=[Part(root=DataPart(data={"results": [1, 2, 3], "status": "complete"}))],
        )

        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        yield Artifact(
            artifact_id=str(3),
            name="image.png",
            parts=[
                Part(
                    root=FilePart(
                        file=FileWithBytes(bytes=base64.b64encode(png_bytes).decode("utf-8"), mime_type="image/png")
                    )
                )
            ],
        )

    async with create_server_with_agent(artifact_producer) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def chunked_artifact_producer(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def chunked_artifact_producer(
        message: Message, context: Context
    ) -> AsyncGenerator[str | ArtifactChunk, Message]:
        # Agent producing chunked artifacts
        yield "Processing chunked artifacts"

        # Create a large text artifact in chunks
        yield ArtifactChunk(
            artifact_id="1",
            name="large-file.txt",
            parts=[Part(root=TextPart(text="This is the first chunk of data.\n"))],
        )

        yield ArtifactChunk(
            artifact_id="1",
            name="large-file.txt",
            parts=[Part(root=TextPart(text="This is the second chunk of data.\n"))],
            last_chunk=False,
        )

        yield ArtifactChunk(
            artifact_id="1",
            name="large-file.txt",
            parts=[Part(root=TextPart(text="This is the final chunk of data.\n"))],
            last_chunk=True,
        )

    async with create_server_with_agent(chunked_artifact_producer) as (server, test_client):
        yield server, test_client
