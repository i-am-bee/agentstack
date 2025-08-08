# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import pytest
from a2a.client import A2AClient
from beeai_sdk.server import Server
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed


@asynccontextmanager
async def run_server(server: Server, port: int) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(
            asyncio.to_thread(
                server.run, port=port, self_registration_client=httpx.AsyncClient(auth=("admin", "test-password"))
            )
        )

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
def create_server_with_agent(free_port):
    """Factory fixture that creates a server with the given agent function."""

    @asynccontextmanager
    async def _create_server(agent_fn):
        server = Server()
        server.agent()(agent_fn)
        async with run_server(server, free_port) as (server, client):
            yield server, client

    return _create_server
