# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import socket
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, closing
from typing import Any

import httpx
import pytest
from a2a.client import A2AClient
from a2a.types import AgentCard
from beeai_sdk.platform import Variables, use_platform_client

logger = logging.getLogger(__name__)


@pytest.fixture()
async def a2a_client_factory() -> Callable[[AgentCard | dict[str, Any]], AsyncIterator[A2AClient]]:
    @asynccontextmanager
    async def a2a_client_factory(agent_card: AgentCard | dict) -> AsyncIterator[A2AClient]:
        async with httpx.AsyncClient(timeout=None, auth=("admin", "test-password")) as client:
            yield A2AClient(client, agent_card)

    return a2a_client_factory


@pytest.fixture()
async def setup_platform_client(test_configuration) -> AsyncIterator[None]:
    async with use_platform_client(
        base_url=test_configuration.server_url, timeout=None, auth=("admin", "test-password")
    ):
        yield None


@pytest.fixture()
def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))  # Bind to any available port
        return int(sock.getsockname()[1])


@pytest.fixture()
async def setup_real_llm(test_configuration, setup_platform_client):
    await Variables.save(
        {
            "LLM_API_BASE": test_configuration.llm_api_base,
            "LLM_API_KEY": test_configuration.llm_api_key.get_secret_value(),
            "LLM_MODEL": test_configuration.llm_model,
        },
    )
