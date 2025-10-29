# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import pytest
from a2a.client import Client
from a2a.types import AgentCard
from agentstack_sdk.platform import PlatformClient, Provider
from agentstack_sdk.server import Server
from agentstack_sdk.server.store.context_store import ContextStore
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from tests.conftest import TestConfiguration


@asynccontextmanager
async def run_server(
    server: Server,
    port: int,
    a2a_client_factory: Callable[[AgentCard | dict[str, Any]], AsyncIterator[Client]],
    context_store: ContextStore | None = None,
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
            async for attempt in AsyncRetrying(stop=stop_after_attempt(20), wait=wait_fixed(0.3), reraise=True):
                with attempt:
                    if not server.server or not server.server.started:
                        raise ConnectionError("Server hasn't started yet")
                    providers = [p for p in await Provider.list() if f":{port}" in p.source]
                    assert len(providers) == 1, "Provider not registered"
                    async with a2a_client_factory(providers[0].agent_card) as client:
                        yield server, client
        finally:
            server.should_exit = True


@pytest.fixture
@pytest.mark.usefixtures("setup_platform_client")
def create_server_with_agent(free_port, test_configuration: TestConfiguration, a2a_client_factory):
    """Factory fixture that creates a server with the given agent function."""

    @asynccontextmanager
    async def _create_server(agent_fn, context_store: ContextStore | None = None):
        server = Server()
        server.agent()(agent_fn)
        async with run_server(
            server, free_port, a2a_client_factory=a2a_client_factory, context_store=context_store
        ) as (server, client):
            yield server, client

    return _create_server
