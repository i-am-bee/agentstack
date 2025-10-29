# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, closing

import httpx
import pytest
from a2a.client import Client, ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Artifact,
    DataPart,
    FilePart,
    FileWithBytes,
    Message,
    TaskStatus,
    TextPart,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from agentstack_sdk.a2a.extensions.ui.agent_detail import AgentDetail
from agentstack_sdk.a2a.types import AgentArtifact, ArtifactChunk, InputRequired, RunYield, RunYieldResume
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.context_store import ContextStore

pytestmark = pytest.mark.e2e


def get_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))  # Bind to any available port
        return int(sock.getsockname()[1])


@asynccontextmanager
async def run_server(
    server: Server, port: int, context_store: ContextStore | None = None
) -> AsyncGenerator[tuple[Server, Client]]:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(asyncio.to_thread(server.run, self_registration=False, port=port, context_store=context_store))

        try:
            async with httpx.AsyncClient(timeout=None) as httpx_client:
                async for attempt in AsyncRetrying(stop=stop_after_attempt(10), wait=wait_fixed(0.1), reraise=True):
                    with attempt:
                        if not server.server or not server.server.started:
                            raise ConnectionError("Server hasn't started yet")
                        base_url = f"http://localhost:{port}"

                        card_resp = await httpx_client.get(f"{base_url}{AGENT_CARD_WELL_KNOWN_PATH}")
                        card_resp.raise_for_status()
                        card = AgentCard.model_validate(card_resp.json())
                        client = ClientFactory(ClientConfig(httpx_client=httpx_client)).create(card=card)
                        yield server, client
        finally:
            server.should_exit = True


@pytest.fixture
def create_server_with_agent():
    """Factory fixture that creates a server with the given agent function."""

    @asynccontextmanager
    async def _create_server(agent_fn, context_store: ContextStore | None = None):
        server = Server()
        server.agent(detail=AgentDetail(interaction_mode="multi-turn"))(agent_fn)
        async with run_server(server, get_free_port(), context_store=context_store) as (server, client):
            yield server, client

    return _create_server


@pytest.fixture
async def echo(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def echo(message: Message, context: RunContext) -> AsyncGenerator[str, Message]:
        for part in message.parts:
            if hasattr(part.root, "text"):
                yield part.root.text

    async with create_server_with_agent(echo) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def slow_echo(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def slow_echo(message: Message, context: RunContext) -> AsyncGenerator[str, Message]:
        # Slower version with delay
        for part in message.parts:
            if hasattr(part.root, "text"):
                await asyncio.sleep(1)
                yield part.root.text

    async with create_server_with_agent(slow_echo) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def awaiter(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def awaiter(message: Message, context: RunContext) -> AsyncGenerator[TaskStatus | str, Message]:
        # Agent that requires input
        yield "Processing initial message..."
        resume_message = yield InputRequired(text="need input")
        yield f"Received resume: {resume_message.parts[0].root.text if resume_message.parts else 'empty'}"

    async with create_server_with_agent(awaiter) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def failer(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def failer(message: Message, context: RunContext) -> AsyncGenerator[RunYield, RunYieldResume]:
        # Agent that raises an error
        yield ValueError("Wrong question buddy!")

    async with create_server_with_agent(failer) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def raiser(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def raiser(message: Message, context: RunContext) -> AsyncGenerator[str, Message]:
        # Another failing agent
        raise RuntimeError("Wrong question buddy!")

    async with create_server_with_agent(raiser) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def artifact_producer(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def artifact_producer(message: Message, context: RunContext) -> AsyncGenerator[str | Artifact, Message]:
        # Agent producing artifacts
        yield "Processing with artifacts"

        # Create artifacts with proper parts structure
        yield AgentArtifact(
            name="text-result.txt",
            parts=[TextPart(text="This is a text artifact result")],
        )

        yield AgentArtifact(
            name="data.json",
            parts=[DataPart(data={"results": [1, 2, 3], "status": "complete"})],
        )

        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        yield AgentArtifact(
            name="image.png",
            parts=[
                FilePart(file=FileWithBytes(bytes=base64.b64encode(png_bytes).decode("utf-8"), mime_type="image/png"))
            ],
        )

    async with create_server_with_agent(artifact_producer) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def chunked_artifact_producer(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def chunked_artifact_producer(
        message: Message, context: RunContext
    ) -> AsyncGenerator[str | ArtifactChunk, Message]:
        # Agent producing chunked artifacts
        yield "Processing chunked artifacts"

        # Create a large text artifact in chunks
        yield ArtifactChunk(
            artifact_id="1",
            name="large-file.txt",
            parts=[TextPart(text="This is the first chunk of data.\n")],
        )

        yield ArtifactChunk(
            artifact_id="1",
            name="large-file.txt",
            parts=[TextPart(text="This is the second chunk of data.\n")],
        )

        yield ArtifactChunk(
            artifact_id="1",
            name="large-file.txt",
            parts=[TextPart(text="This is the final chunk of data.\n")],
            last_chunk=True,
        )

    async with create_server_with_agent(chunked_artifact_producer) as (server, test_client):
        yield server, test_client
