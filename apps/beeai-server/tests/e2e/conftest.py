import logging
from typing import AsyncIterator

import httpx
import pytest_asyncio
from acp_sdk.client import Client


logger = logging.getLogger(__name__)


@pytest_asyncio.fixture()
async def api_client(test_configuration) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        base_url=f"{test_configuration.server_url.rstrip('/')}/api/v1", timeout=None
    ) as client:
        yield client


@pytest_asyncio.fixture()
async def acp_client(api_client, test_configuration) -> AsyncIterator[Client]:
    async with Client(base_url=f"{str(test_configuration.server_url).rstrip('/')}/api/v1/acp") as client:
        yield client


@pytest_asyncio.fixture()
async def setup_real_llm(api_client, test_configuration):
    env = {
        "LLM_API_BASE": test_configuration.llm_api_base,
        "LLM_API_KEY": test_configuration.llm_api_key.get_secret_value(),
        "LLM_MODEL": test_configuration.llm_model,
    }
    await api_client.put("variables", json={"env": env})
