# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import uuid
from collections.abc import Callable

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from kink import Container
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from agentstack_server.application import app
from agentstack_server.utils.utils import utc_now


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def agentstack_server() -> Callable[[Container | None], TestClient]:
    client: TestClient | None = None

    def server_factory(dependency_overrides: Container | None = None) -> TestClient:
        nonlocal client
        server_app = app(dependency_overrides=dependency_overrides, enable_crons=False)
        client = TestClient(server_app)
        return client

    yield server_factory


@pytest.fixture
async def admin_user(db_transaction: AsyncConnection) -> uuid.UUID:
    uid = uuid.uuid4()
    await db_transaction.execute(
        text("INSERT INTO users (id, email, created_at, role) VALUES (:id, :email, :created_at, :role)"),
        [
            {"id": uid, "email": "dummy@agentstack.dev", "created_at": utc_now(), "role": "admin"},
        ],
    )
    return uid
