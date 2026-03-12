# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from pprint import pprint
from typing import Any

import async_lru
import pytest
from agentstack_sdk.platform import ModelProviderType
from kink import di
from pydantic import Secret, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from agentstack_server.infrastructure.persistence.repositories.db_metadata import metadata

# Disable async_lru event loop check in tests
async_lru._LRUCacheWrapper._check_loop = lambda self, loop: None


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    kubeconfig: Path = Path.home() / ".agentstack/lima/agentstack-local-dev/copied-from-guest/kubeconfig.yaml"
    llm_api_base: Secret[str] = Secret("http://localhost:11434/v1")
    llm_model: str = "ollama:gpt-oss:20b"
    embedding_model: str = "ollama:nomic-embed-text:latest"
    llm_api_key: Secret[str] = Secret("dummy")
    test_agent_image: str = "registry.cr-system.svc.cluster.local:5000/chat-test:latest"
    server_url: str = "http://agentstack-api.localtest.me:8080"
    db_url: str = "postgresql+asyncpg://agentstack-user:password@postgresql:5432/agentstack"
    keycloak_url: str = "http://localhost:8336"

    @computed_field
    @property
    def llm_provider_type(self) -> ModelProviderType:
        return ModelProviderType(self.llm_model.split(":", maxsplit=1)[0])

    @model_validator(mode="after")
    def set_kubeconfig_env(self):
        os.environ.setdefault("KUBECONFIG", str(self.kubeconfig))
        return self


@pytest.fixture(scope="session")
def test_configuration() -> Configuration:
    return Configuration()


def pytest_configure(config):
    expr = config.getoption("markexpr")

    config = Configuration()  # validate config and set KUBECONFIG env

    if "e2e" in expr or "integration" in expr:
        print("\n\nRunning with configuration:")
        pprint(config.model_dump())
        print()


@pytest.fixture()
async def db_transaction(test_configuration):
    """Auto-rollback connection"""
    engine = create_async_engine(test_configuration.db_url)
    async with engine.connect() as connection, connection.begin() as transaction:
        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest.fixture(scope="session")
def clean_up_fn(test_configuration):
    async def _fn():
        engine = create_async_engine(test_configuration.db_url)
        # Clean all tables
        async with engine.connect() as connection:
            # TODO: drop all users except dummy ones
            for table in metadata.tables.keys() - {"users"}:
                await connection.execute(text(f'TRUNCATE TABLE public."{table}" RESTART IDENTITY CASCADE'))

            # Drop all vector_db tables
            vecdb = await connection.execute(text("SELECT tablename from pg_tables where schemaname = 'vector_db'"))
            for row in vecdb.fetchall():
                await connection.execute(text(f"DROP TABLE vector_db.{row.tablename} CASCADE"))

            await connection.commit()
        print("Cleaned up")

    return _fn


@pytest.fixture()
async def clean_up(clean_up_fn):
    """Truncate all tables after each test."""
    try:
        yield
    finally:
        await clean_up_fn()


@pytest.fixture()
def override_global_dependency():
    @contextmanager
    def override_global_dependency[T](cls: type[T], value: T | Any):
        orig_value = di[cls] if cls in di else None  # noqa: SIM401
        di[cls] = value
        try:
            yield
        finally:
            di[cls] = orig_value

    return override_global_dependency
