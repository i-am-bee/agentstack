# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import pytest
from a2a.client import Client, ClientFactory
from a2a.types import AgentCard
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from beeai_sdk.platform import PlatformClient
from beeai_sdk.server import Server
from beeai_sdk.server.store.context_store import ContextStore
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from tests.conftest import TestConfiguration


@asynccontextmanager
async def run_server(
    server: Server, port: int, context_store: ContextStore | None = None
) -> AsyncGenerator[tuple[Server, Client]]:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(
            asyncio.to_thread(
                server.run,
                port=port,
                self_registration_client_factory=lambda: PlatformClient(auth=("admin", "test-password")),
                context_store=context_store,
            )
        )

        try:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(10), wait=wait_fixed(0.1), reraise=True):
                with attempt:
                    if not server.server or not server.server.started:
                        raise ConnectionError("Server hasn't started yet")
                    base_url = f"http://localhost:{port}"
                    async with httpx.AsyncClient(timeout=None) as httpx_client:
                        from a2a.client import ClientConfig

                        card_resp = await httpx_client.get(base_url + AGENT_CARD_WELL_KNOWN_PATH)
                        card_resp.raise_for_status()
                        card = AgentCard.model_validate(card_resp.json())
                        client = ClientFactory(ClientConfig(httpx_client=httpx_client)).create(card)
                        yield server, client
        finally:
            server.should_exit = True


@pytest.fixture
def create_server_with_agent(free_port, test_configuration: TestConfiguration):
    """Factory fixture that creates a server with the given agent function."""

    @asynccontextmanager
    async def _create_server(agent_fn, context_store: ContextStore | None = None):
        server = Server()
        server.agent()(agent_fn)
        async with run_server(server, free_port, context_store=context_store) as (server, client):
            yield server, client

    return _create_server
