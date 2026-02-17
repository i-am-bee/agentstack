# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
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
from pydantic import Secret
from tenacity import retry, stop_after_delay, wait_fixed

DEFAULT_PORT = 8000


class RunningExample(NamedTuple):
    client: Client
    context: Context
    context_token: ContextToken
    provider: Provider
    agent_card: AgentCard


def run_process(
    example_dir_path: str, port: int, llm_model: str | None = None, llm_api_key: Secret[str] | None = None
) -> subprocess.Popen:
    cwd = f"../../examples/{example_dir_path}"
    print(f"Running example in {cwd}")
    return subprocess.Popen(
        ["uv", "run", "server"],
        cwd=cwd,
        env={
            **os.environ,
            "PORT": str(port),
            "PRODUCTION_MODE": "true",
            **({"OPENAI_API_KEY": llm_api_key.get_secret_value()} if llm_api_key else {}),
            **({"LLM_MODEL": llm_model} if llm_model else {}),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )


def kill_process(process: subprocess.Popen) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

    stdout, stderr = process.communicate(timeout=10)
    if stdout:
        print(f"--- example stdout ---\n{stdout.decode(errors='replace')}")
    if stderr:
        print(f"--- example stderr ---\n{stderr.decode(errors='replace')}")


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
    llm_model: str | None = None,
    llm_api_key: Secret[str] | None = None,
) -> AsyncGenerator[RunningExample]:
    process = run_process(example_dir_path, port, llm_model, llm_api_key)
    try:
        example_url = f"http://localhost:{port}"

        # load agent card from expected location
        agent_card = await _get_agent_card(example_url)

        # create provider for the agent
        provider = await Provider.create(location=example_url, agent_card=agent_card)

        # create context for the example
        context = await Context.create()

        # generate context token with global permissions for the provider (agent)
        context_token = await context.generate_token(
            providers={provider.id},
            grant_global_permissions=Permissions(llm={"*"}),
            grant_context_permissions=ContextPermissions(context_data={"*"}),
        )

        async with a2a_client_factory(provider.agent_card, context_token) as a2a_client:
            yield RunningExample(a2a_client, context, context_token, provider, agent_card)
    finally:
        kill_process(process)
