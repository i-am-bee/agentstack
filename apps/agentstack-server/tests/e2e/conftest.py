# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import socket
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, closing, suppress
from typing import Any

import httpx
import pytest
from a2a.client import Client, ClientConfig, ClientEvent, ClientFactory
from a2a.types import AgentCard, Message, Task
from agentstack_sdk.platform import ModelProvider, SystemConfiguration, use_platform_client
from agentstack_sdk.platform.context import ContextToken
from keycloak import KeycloakAdmin

logger = logging.getLogger(__name__)


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


@pytest.fixture()
async def setup_platform_client(test_configuration, test_admin) -> AsyncIterator[None]:
    async with use_platform_client(base_url=test_configuration.server_url, timeout=None, auth=test_admin):
        yield None


@pytest.fixture()
def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))  # Bind to any available port
        return int(sock.getsockname()[1])


@pytest.fixture()
async def setup_real_llm(test_configuration, setup_platform_client):
    try:
        await ModelProvider.create(
            name="test_config",
            type=test_configuration.llm_provider_type,
            base_url=test_configuration.llm_api_base.get_secret_value(),
            api_key=test_configuration.llm_api_key.get_secret_value(),
        )
    except httpx.HTTPStatusError as ex:
        with suppress(Exception):
            ex = Exception(str(f"Failed to setup LLM - {ex}\n{json.dumps(ex.response.text, indent=2)}"))
        raise ex
    await SystemConfiguration.update(
        default_llm_model=test_configuration.llm_model, default_embedding_model=test_configuration.embedding_model
    )


@pytest.fixture(scope="session")
def keycloak_admin(test_configuration) -> KeycloakAdmin:
    """Keycloak Admin Client"""
    return KeycloakAdmin(
        server_url=test_configuration.keycloak_url,
        username="admin",
        password="admin",
        realm_name="agentstack",
        user_realm_name="master",
        verify=True,
    )


def _create_test_user(keycloak_admin: KeycloakAdmin, username: str, role: str | None = None):
    # Check if user exists
    user_id = keycloak_admin.get_user_id(username)
    if user_id:
        keycloak_admin.delete_user(user_id)

    # Create user with credentials
    new_user_id = keycloak_admin.create_user(
        {
            "email": f"{username}@beeai.dev",
            "username": username,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{"type": "password", "value": f"{username}-password", "temporary": False}],
            "firstName": "Test",
            "lastName": "User",
        }
    )
    keycloak_admin.set_user_password(new_user_id, f"{username}-password", temporary=False)
    if role:
        [role] = [r for r in keycloak_admin.get_realm_roles() if r["name"] == role]
        keycloak_admin.assign_realm_roles(new_user_id, role)
    return keycloak_admin.get_user(new_user_id)


@pytest.fixture(scope="session")
def test_admin(keycloak_admin) -> tuple[str, str]:
    username = "testadmin"
    _create_test_user(keycloak_admin, username, "agentstack-admin")
    try:
        yield username, f"{username}-password"
    finally:
        if user_id := keycloak_admin.get_user_id(username):
            keycloak_admin.delete_user(user_id)


@pytest.fixture(scope="session")
def test_user(keycloak_admin) -> tuple[str, str]:
    username = "testuser"
    _create_test_user(keycloak_admin, username)
    try:
        yield username, f"{username}-password"
    finally:
        if user_id := keycloak_admin.get_user_id(username):
            keycloak_admin.delete_user(user_id)


@pytest.fixture(scope="session")
def test_second_user(keycloak_admin) -> tuple[str, str]:
    username = "testuser2"
    _create_test_user(keycloak_admin, username)
    try:
        yield username, f"{username}-password"
    finally:
        if user_id := keycloak_admin.get_user_id(username):
            keycloak_admin.delete_user(user_id)
