# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
import pytest_asyncio
from a2a.client import A2AClient
from a2a.types import AgentCard
from beeai_sdk.platform import Variables, use_platform_client

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture()
async def a2a_client_factory() -> Callable[[AgentCard | dict[str, Any]], AsyncIterator[A2AClient]]:
    @asynccontextmanager
    async def a2a_client_factory(agent_card: AgentCard | dict) -> AsyncIterator[A2AClient]:
        async with httpx.AsyncClient(timeout=None) as client:
            yield A2AClient(client, agent_card)

    return a2a_client_factory


@pytest_asyncio.fixture()
async def setup_platform_client(test_configuration) -> AsyncIterator[None]:
    async with use_platform_client(
        base_url=test_configuration.server_url, timeout=None, auth=("admin", "test-password")
    ):
        yield None


@pytest_asyncio.fixture()
@pytest.mark.usefixtures("setup_platform_client")
async def setup_real_llm(test_configuration):
    await Variables.save(
        {
            "LLM_API_BASE": test_configuration.llm_api_base,
            "LLM_API_KEY": test_configuration.llm_api_key.get_secret_value(),
            "LLM_MODEL": test_configuration.llm_model,
        }
    )
