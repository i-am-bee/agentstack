# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import signal
import subprocess
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, NamedTuple

import httpx
import pytest
from a2a.client import Client, ClientEvent
from a2a.types import AgentCard, Message, Task
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from agentstack_sdk.platform import Provider
from agentstack_sdk.platform.context import Context, ContextPermissions, ContextToken, Permissions
from tenacity import retry, stop_after_delay, wait_fixed

DEFAULT_PORT = 8000


class RunningExample(NamedTuple):
    client: Client
    context: Context
    context_token: ContextToken
    provider: Provider


def run_process(example_dir_path: str, port: int) -> subprocess.Popen:
    cwd = f"../../examples/{example_dir_path}"
    print(f"Running example in {cwd}")
    return subprocess.Popen(
        ["uv", "run", "server"],
        cwd=cwd,
        env={**os.environ, "PORT": str(port), "PRODUCTION_MODE": "true"},
        preexec_fn=os.setsid,
    )


def kill_process(process: subprocess.Popen) -> None:
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait()


@retry(stop=stop_after_delay(30), wait=wait_fixed(0.5))
async def _get_agent_card(agent_url: str):
    async with httpx.AsyncClient(timeout=None) as httpx_client:
        card_resp = await httpx_client.get(f"{agent_url}{AGENT_CARD_WELL_KNOWN_PATH}")
        card_resp.raise_for_status()
        card = AgentCard.model_validate(card_resp.json())
        return card


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


@asynccontextmanager
async def run_example(
    example_dir_path: str,
    a2a_client_factory: Callable[[AgentCard | dict[str, Any], ContextToken], AsyncIterator[Client]],
    port: int = DEFAULT_PORT,
) -> AsyncGenerator[RunningExample]:
    process = run_process(example_dir_path, port)
    try:
        example_url = f"http://localhost:{port}"
        agent_card = await _get_agent_card(example_url)
        provider = await Provider.create(location=example_url, agent_card=agent_card)

        context = await Context.create()
        context_token = await context.generate_token(
            providers={provider.id},
            grant_global_permissions=Permissions(llm={"*"}),
            grant_context_permissions=ContextPermissions(context_data={"*"}),
        )

        async with a2a_client_factory(provider.agent_card, context_token) as a2a_client:
            yield RunningExample(a2a_client, context, context_token, provider)
    finally:
        kill_process(process)
