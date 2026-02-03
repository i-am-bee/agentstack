# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import signal
import subprocess
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
from a2a.client import Client, ClientConfig, ClientEvent, ClientFactory
from a2a.types import AgentCard, Message, Task
from agentstack_sdk.platform import Provider
from agentstack_sdk.platform.context import Context, ContextToken
from tenacity import retry, stop_after_delay, wait_fixed

DEFAULT_PORT = 8000


def run_example_process(example_name: str, port: int) -> subprocess.Popen:
    cwd = f"../../examples/{example_name}"
    print(f"Running example in {cwd}")
    return subprocess.Popen(
        ["uv", "run", "server"],
        cwd=cwd,
        env={**os.environ, "PORT": str(port)},
        preexec_fn=os.setsid,
    )


def get_example_url(example_name: str, port: int = DEFAULT_PORT) -> str:
    return f"http://localhost:{port}/#{example_name.replace('-', '_')}_example"


def kill_process(process: subprocess.Popen) -> None:
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait()


@retry(stop=stop_after_delay(30), wait=wait_fixed(0.5))
async def _wait_for_ready(example_url: str):
    providers = await Provider.list()
    provider = next((p for p in providers if p.source == example_url), None)
    assert provider, "Provider not registered yet"
    return provider


@pytest.fixture
def get_final_task_from_stream() -> Callable[[AsyncIterator[ClientEvent | Message]], Awaitable[Task]]:
    async def fn(stream: AsyncIterator[ClientEvent | Message]) -> Task:
        """Helper to extract the final task from a client.send_message stream."""
        final_task = None
        async for event in stream:
            match event:
                case (task, None):
                    final_task = task
                case (task, _):
                    final_task = task
        return final_task

    return fn


@pytest.fixture()
async def a2a_client_factory() -> Callable[[AgentCard | dict[str, Any], ContextToken], AsyncIterator[Client]]:
    @asynccontextmanager
    async def a2a_client_factory(agent_card: AgentCard | dict, context_token: ContextToken) -> AsyncIterator[Client]:
        token = context_token.token.get_secret_value()
        async with httpx.AsyncClient(timeout=None, headers={"Authorization": f"Bearer {token}"}) as client:
            yield ClientFactory(ClientConfig(httpx_client=client)).create(card=agent_card)

    return a2a_client_factory


@asynccontextmanager
async def example_process(
    example_name: str,
    a2a_client_factory: Callable[[AgentCard | dict[str, Any], ContextToken], AsyncIterator[Client]],
    port: int = DEFAULT_PORT,
) -> AsyncGenerator[tuple[subprocess.Popen, Client, Context]]:
    process = run_example_process(example_name, port)
    try:
        provider = await _wait_for_ready(get_example_url(example_name, port))

        context = await Context.create()
        context_token = await context.generate_token(providers={provider.id})

        async with a2a_client_factory(provider.agent_card, context_token) as a2a_client:
            yield process, a2a_client, context
    finally:
        kill_process(process)
