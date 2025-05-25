import asyncio
import logging
import os
import re
from collections.abc import Callable
from pathlib import Path
from pprint import pprint

import httpx
import kr8s
import pytest
import pytest_asyncio
from acp_sdk.client import Client
from pydantic import model_validator, Secret
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

logger = logging.getLogger(__name__)


class TestConfiguration(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    kubeconfig: Path = Path.home() / ".beeai/lima/e2e-test/copied-from-guest/kubeconfig.yaml"
    llm_api_base: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.1"
    llm_api_key: Secret[str] = Secret("dummy")
    server_url: str = "http://beeai-platform-svc:8333"
    db_url: str = "postgresql+asyncpg://beeai-user:password@postgresql:5432/beeai"

    @model_validator(mode="after")
    def set_kubeconfig_env(self):
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig))
        return self


CONFIGURATION = TestConfiguration()
print("\n\nRunning with configuration:")
pprint(CONFIGURATION.model_dump())
print()


async def _get_kr8s_client():
    api = await kr8s.asyncio.api(namespace="beeai")
    kubeconfig = api.auth.kubeconfig
    kubeconfig_regex = r".*/.beeai/(lima|docker)/e2e-test/copied-from-guest/kubeconfig.yaml$"
    if not re.match(kubeconfig_regex, str(kubeconfig.path)):
        raise ValueError(
            f"Preventing e2e tests run with invalid kubeconfig path.\n"
            f"actual: {kubeconfig.path}\n"
            f"expected: {kubeconfig_regex}"
        )
    return api


def pytest_sessionstart(session):
    """Validate that tests are running against the e2e-test VM"""
    asyncio.run(_get_kr8s_client())


@pytest_asyncio.fixture()
async def kr8s_client():
    return await _get_kr8s_client()


@pytest.fixture()
def api_client() -> Callable[[], httpx.AsyncClient]:
    def client_factory():
        return httpx.AsyncClient(base_url=f"{CONFIGURATION.server_url.rstrip('/')}/api/v1")

    return client_factory


@pytest.fixture()
def acp_client(api_client) -> Callable[[], Client]:
    def client_factory():
        return Client(base_url=f"{str(api_client().base_url).rstrip('/')}/acp")

    return client_factory


@pytest_asyncio.fixture()
async def setup_real_llm(api_client):
    env = {
        "LLM_API_BASE": CONFIGURATION.llm_api_base,
        "LLM_API_KEY": CONFIGURATION.llm_api_key.get_secret_value(),
        "LLM_MODEL": CONFIGURATION.llm_model,
    }
    async with api_client() as client:
        await client.put("variables", json={"env": env})


@pytest_asyncio.fixture(autouse=True)
async def auto_clean(kr8s_client):
    """Truncate all tables after each test."""
    engine = create_async_engine(CONFIGURATION.db_url)
    try:
        yield
    finally:
        # Clean all tables
        async with engine.connect() as connection:
            for table in metadata.tables:
                await connection.execute(text(f'TRUNCATE TABLE public."{table}" RESTART IDENTITY CASCADE'))
            await connection.commit()
        # Clean all deployments
        async for deployment in kr8s_client.get(kind="deploy"):
            deployment.labels.app.startswith("beeai-provider-") and await deployment.delete()
        print("Cleaned up")
