# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# Testing proxy server capabilities, using tests from a2a:
# https://github.com/a2aproject/a2a-python/blob/main/tests/server/test_integration.py
from __future__ import annotations

import asyncio
import contextlib
import socket
import time
import uuid
from contextlib import closing, suppress
from threading import Thread
from unittest import mock

import pytest
import uvicorn
from a2a.server.apps import (
    A2AFastAPIApplication,
    A2AStarletteApplication,
)
from a2a.server.context import ServerCallContext
from a2a.server.jsonrpc_models import (
    InternalError,
    InvalidParamsError,
    InvalidRequestError,
    JSONParseError,
    MethodNotFoundError,
)
from a2a.types.a2a_pb2 import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Artifact,
    Message,
    Part,
    PushNotificationConfig,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskPushNotificationConfig,
    TaskState,
    TaskStatus,
)
from a2a.utils import (
    AGENT_CARD_WELL_KNOWN_PATH,
)

# These constants were removed in a2a-sdk v1; tests using them are skipped
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"
PREV_AGENT_CARD_WELL_KNOWN_PATH = "/.well-known/agent.json"
from a2a.utils.errors import UnsupportedOperationError
from fastapi import FastAPI
from google.protobuf.struct_pb2 import Struct, Value
from httpx import Client, ReadTimeout
from sqlalchemy import text
from starlette.applications import Starlette
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
    SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from agentstack_server.infrastructure.persistence.repositories.user import users_table

pytestmark = pytest.mark.e2e

# === TEST SETUP ===

MINIMAL_AGENT_SKILL = AgentSkill(
    id="skill-123",
    name="Recipe Finder",
    description="Finds recipes",
    tags=["cooking"],
)

AGENT_CAPS = AgentCapabilities(push_notifications=True, streaming=True)

MINIMAL_AGENT_CARD_DATA = AgentCard(
    capabilities=AGENT_CAPS,
    default_input_modes=["text/plain"],
    default_output_modes=["application/json"],
    description="Test Agent",
    name="TestAgent",
    skills=[MINIMAL_AGENT_SKILL],
    supported_interfaces=[AgentInterface(url="http://example.com/agent", protocol_binding="JSONRPC")],
    version="1.0",
)

EXTENDED_AGENT_SKILL = AgentSkill(
    id="skill-extended",
    name="Extended Skill",
    description="Does more things",
    tags=["extended"],
)

EXTENDED_AGENT_CARD_DATA = AgentCard(
    capabilities=AGENT_CAPS,
    default_input_modes=["text/plain"],
    default_output_modes=["application/json"],
    description="Test Agent with more details",
    name="TestAgent Extended",
    skills=[MINIMAL_AGENT_SKILL, EXTENDED_AGENT_SKILL],
    supported_interfaces=[AgentInterface(url="http://example.com/agent", protocol_binding="JSONRPC")],
    version="1.0",
)

TEXT_PART_DATA = Part(text="Hello")

# For proto, Part.data takes a Value(struct_value=Struct)
_struct = Struct()
_struct.update({"key": "value"})
DATA_PART = Part(data=Value(struct_value=_struct))

MINIMAL_MESSAGE_USER = Message(
    role=Role.ROLE_USER,
    parts=[TEXT_PART_DATA],
    message_id="msg-123",
)

MINIMAL_TASK_STATUS = TaskStatus(state=TaskState.TASK_STATE_SUBMITTED)

FULL_TASK_STATUS = TaskStatus(
    state=TaskState.TASK_STATE_WORKING,
    message=MINIMAL_MESSAGE_USER,
)


@pytest.fixture
def agent_card():
    return MINIMAL_AGENT_CARD_DATA


@pytest.fixture
def extended_agent_card_fixture():
    return EXTENDED_AGENT_CARD_DATA


@pytest.fixture
def handler():
    handler = mock.AsyncMock()
    handler.on_message_send = mock.AsyncMock()
    handler.on_cancel_task = mock.AsyncMock()
    handler.on_get_task = mock.AsyncMock()
    handler.set_push_notification = mock.AsyncMock()
    handler.get_push_notification = mock.AsyncMock()
    handler.on_message_send_stream = mock.Mock()
    handler.on_subscribe_to_task = mock.Mock()
    return handler


@pytest.fixture
def app(agent_card: AgentCard, handler: mock.AsyncMock):
    return A2AStarletteApplication(agent_card, handler)


@pytest.fixture
def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))  # Bind to any available port
        return int(sock.getsockname()[1])


@pytest.fixture
def create_test_server(free_port: int, app: A2AStarletteApplication, test_admin, test_configuration, clean_up_fn):
    server_instance: uvicorn.Server | None = None
    thread: Thread | None = None
    for interface in app.agent_card.supported_interfaces:
        interface.url = f"http://host.docker.internal:{free_port}"

    def _create_test_server(custom_app: Starlette | FastAPI | None = None) -> Client:
        custom_app = custom_app or app.build()
        nonlocal server_instance
        config = uvicorn.Config(app=custom_app, port=free_port, log_level="warning")
        server_instance = uvicorn.Server(config)

        def run_server():
            with contextlib.suppress(KeyboardInterrupt):
                server_instance.run()

        thread = Thread(target=run_server, name="test-server")
        thread.start()
        while not server_instance.started:
            time.sleep(0.1)

        with Client(base_url=f"{test_configuration.server_url}/api/v1", auth=test_admin, timeout=None) as client:
            for _attempt in range(20):
                with suppress(ReadTimeout):
                    resp = client.post(
                        "providers",
                        json={"location": f"http://host.docker.internal:{free_port}"},
                        timeout=2,
                    )
                    if not resp.is_error:
                        provider_id = resp.json()["id"]
                        break
                time.sleep(0.5)
            else:
                error = "unknown error"
                with contextlib.suppress(Exception):
                    error = resp.json()
                raise RuntimeError(f"Server did not start or register itself correctly: {error}")

        return Client(
            base_url=f"{test_configuration.server_url}/api/v1/a2a/{provider_id}", auth=test_admin, timeout=None
        )

    try:
        yield _create_test_server
    finally:
        asyncio.run(clean_up_fn())
        if server_instance:
            server_instance.should_exit = True
        if thread:
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Server did not exit after 5 seconds")


@pytest.fixture
async def ensure_mock_task(test_admin, db_transaction, clean_up):
    res = await db_transaction.execute(users_table.select().where(users_table.c.email == f"{test_admin[0]}@beeai.dev"))
    admin_user = res.fetchone().id
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, NOW(), NOW())"
        ),
        {"task_id": "task1", "created_by": admin_user, "provider_id": uuid.uuid4()},
    )
    await db_transaction.commit()


@pytest.fixture
def client(create_test_server):
    """Create a proxy client pointing at the registered agent server."""
    return create_test_server()


# --------------------------------------- TESTS PORTED FROM A2A TEST SUITE ---------------------------------------------
# === BASIC FUNCTIONALITY TESTS ===


def test_agent_card_endpoint(client: Client, agent_card: AgentCard):
    """Test the agent card endpoint returns expected data."""
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name
    assert data["version"] == agent_card.version
    assert "streaming" in data["capabilities"]


@pytest.mark.skip(reason="Extended agent card endpoint routing is not supported through the proxy.")
def test_authenticated_extended_agent_card_endpoint_not_supported(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test extended card endpoint returns 404 if not supported by main card."""
    agent_card.capabilities.extended_agent_card = False
    app_instance = A2AStarletteApplication(agent_card, handler)
    client = TestClient(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 404


@pytest.mark.skip(reason="Deprecated agent card routing is not applicable to the proxy.")
def test_agent_card_default_endpoint_has_deprecated_route(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test agent card deprecated route is available for default route."""
    app_instance = A2AStarletteApplication(agent_card, handler)
    client = TestClient(app_instance.build())
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name
    response = client.get(PREV_AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


@pytest.mark.skip(reason="Deprecated agent card routing is not applicable to the proxy.")
def test_agent_card_custom_endpoint_has_no_deprecated_route(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test agent card deprecated route is not available for custom route."""
    app_instance = A2AStarletteApplication(agent_card, handler)
    client = TestClient(app_instance.build(agent_card_url="/my-agent"))
    response = client.get("/my-agent")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name
    response = client.get(PREV_AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 404


@pytest.mark.skip(reason="Extended agent card endpoint routing is not supported through the proxy.")
def test_authenticated_extended_agent_card_endpoint_not_supported_fastapi(
    agent_card: AgentCard, handler: mock.AsyncMock
):
    """Test extended card endpoint returns 404 if not supported by main card."""
    agent_card.capabilities.extended_agent_card = False
    app_instance = A2AFastAPIApplication(agent_card, handler)
    client = TestClient(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 404


@pytest.mark.skip(reason="Extended agent card is not supported at the moment. # TODO")
def test_authenticated_extended_agent_card_endpoint_supported_with_specific_extended_card_starlette(
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test extended card endpoint returns the specific extended card when provided."""
    agent_card.capabilities.extended_agent_card = True
    app_instance = A2AStarletteApplication(agent_card, handler, extended_agent_card=extended_agent_card_fixture)
    client = TestClient(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == extended_agent_card_fixture.name
    assert data["version"] == extended_agent_card_fixture.version
    assert len(data["skills"]) == len(extended_agent_card_fixture.skills)
    assert any(skill["id"] == "skill-extended" for skill in data["skills"]), "Extended skill not found in served card"


@pytest.mark.skip(reason="Extended agent card is not supported at the moment. # TODO")
def test_authenticated_extended_agent_card_endpoint_supported_with_specific_extended_card_fastapi(
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test extended card endpoint returns the specific extended card when provided."""
    agent_card.capabilities.extended_agent_card = True
    app_instance = A2AFastAPIApplication(agent_card, handler, extended_agent_card=extended_agent_card_fixture)
    client = TestClient(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == extended_agent_card_fixture.name
    assert data["version"] == extended_agent_card_fixture.version
    assert len(data["skills"]) == len(extended_agent_card_fixture.skills)
    assert any(skill["id"] == "skill-extended" for skill in data["skills"]), "Extended skill not found in served card"


@pytest.mark.skip(reason="Custom agent card URLs are not supported through the proxy.")
def test_agent_card_custom_url(app: A2AStarletteApplication, agent_card: AgentCard):
    """Test the agent card endpoint with a custom URL."""
    client = TestClient(app.build(agent_card_url="/my-agent"))
    response = client.get("/my-agent")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


@pytest.mark.skip(reason="Custom RPC URLs are not supported through the proxy.")
def test_starlette_rpc_endpoint_custom_url(app: A2AStarletteApplication, handler: mock.AsyncMock):
    """Test the RPC endpoint with a custom URL."""
    task = Task(id="task1", context_id="ctx1", status=MINIMAL_TASK_STATUS)
    handler.on_get_task.return_value = task
    client = TestClient(app.build(rpc_url="/api/rpc"))
    response = client.post(
        "/api/rpc",
        json={"jsonrpc": "2.0", "id": "123", "method": "GetTask", "params": {"id": "task1"}},
    )
    assert response.status_code == 200
    assert response.json()["result"]["id"] == "task1"


@pytest.mark.skip(reason="Custom RPC URLs are not supported through the proxy.")
def test_fastapi_rpc_endpoint_custom_url(app: A2AFastAPIApplication, handler: mock.AsyncMock):
    """Test the RPC endpoint with a custom URL."""
    task = Task(id="task1", context_id="ctx1", status=MINIMAL_TASK_STATUS)
    handler.on_get_task.return_value = task
    client = TestClient(app.build(rpc_url="/api/rpc"))
    response = client.post(
        "/api/rpc",
        json={"jsonrpc": "2.0", "id": "123", "method": "GetTask", "params": {"id": "task1"}},
    )
    assert response.status_code == 200
    assert response.json()["result"]["id"] == "task1"


@pytest.mark.skip(reason="Custom routes are not supported through the proxy.")
def test_starlette_build_with_extra_routes(app: A2AStarletteApplication, agent_card: AgentCard):
    """Test building the app with additional routes."""

    def custom_handler(request):
        return JSONResponse({"message": "Hello"})

    extra_route = Route("/hello", custom_handler, methods=["GET"])
    client = TestClient(app.build(routes=[extra_route]))
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    assert response.json()["name"] == agent_card.name


@pytest.mark.skip(reason="Custom routes are not supported through the proxy.")
def test_fastapi_build_with_extra_routes(app: A2AFastAPIApplication, agent_card: AgentCard):
    """Test building the app with additional routes."""

    def custom_handler(request):
        return JSONResponse({"message": "Hello"})

    extra_route = Route("/hello", custom_handler, methods=["GET"])
    client = TestClient(app.build(routes=[extra_route]))
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    assert response.json()["name"] == agent_card.name
    response = client.get(PREV_AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    assert response.json()["name"] == agent_card.name


@pytest.mark.skip(reason="Custom agent card paths are not supported through the proxy.")
def test_fastapi_build_custom_agent_card_path(app: A2AFastAPIApplication, agent_card: AgentCard):
    """Test building the app with a custom agent card path."""
    client = TestClient(app.build(agent_card_url="/agent-card"))
    response = client.get("/agent-card")
    assert response.status_code == 200
    assert response.json()["name"] == agent_card.name
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 404
    response = client.get(PREV_AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 404


# === REQUEST METHODS TESTS ===


def test_send_message(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test sending a message."""
    # Prepare mock response
    mock_task = Task(
        id="task1",
        context_id="session-xyz",
        status=MINIMAL_TASK_STATUS,
    )
    handler.on_message_send.return_value = mock_task

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "SendMessage",
            "params": {
                "message": {
                    "role": "ROLE_AGENT",
                    "parts": [{"text": "Hello"}],
                    "messageId": "111",
                    "taskId": "task1",
                    "contextId": "session-xyz",
                }
            },
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["task"]["id"] == "task1"
    assert data["result"]["task"]["status"]["state"] == "TASK_STATE_SUBMITTED"

    # Verify handler was called
    handler.on_message_send.assert_awaited_once()


def test_cancel_task(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test cancelling a task."""
    # Setup mock response
    task = Task(id="task1", context_id="ctx1", status=TaskStatus(state=TaskState.TASK_STATE_CANCELED))
    handler.on_cancel_task.return_value = task

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "CancelTask",
            "params": {"id": "task1"},
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["id"] == "task1"
    assert data["result"]["status"]["state"] == "TASK_STATE_CANCELED"

    # Verify handler was called
    handler.on_cancel_task.assert_awaited_once()


def test_get_task(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test getting a task."""
    # Setup mock response
    task = Task(id="task1", context_id="ctx1", status=MINIMAL_TASK_STATUS)
    handler.on_get_task.return_value = task

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "GetTask",
            "params": {"id": "task1"},
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["id"] == "task1"

    # Verify handler was called
    handler.on_get_task.assert_awaited_once()


def test_set_push_notification_config(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test setting push notification configuration."""
    # Setup mock response
    task_push_config = TaskPushNotificationConfig(
        task_id="t2",
        push_notification_config=PushNotificationConfig(url="https://example.com", token="secret-token"),
    )
    handler.on_create_task_push_notification_config.return_value = task_push_config

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "CreateTaskPushNotificationConfig",
            "params": {
                "task_id": "task1",
                "config": {
                    "url": "https://example.com",
                    "token": "secret-token",
                },
            },
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["pushNotificationConfig"]["token"] == "secret-token"

    # Verify handler was called
    handler.on_create_task_push_notification_config.assert_awaited_once()


def test_get_push_notification_config(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test getting push notification configuration."""
    # Setup mock response
    task_push_config = TaskPushNotificationConfig(
        task_id="task1",
        push_notification_config=PushNotificationConfig(url="https://example.com", token="secret-token"),
    )

    handler.on_get_task_push_notification_config.return_value = task_push_config

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "GetTaskPushNotificationConfig",
            "params": {
                "task_id": "task1",
                "id": "pushNotificationConfig",
            },
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["pushNotificationConfig"]["token"] == "secret-token"

    # Verify handler was called
    handler.on_get_task_push_notification_config.assert_awaited_once()


@pytest.mark.skip(reason="Custom authentication middleware cannot be injected through the proxy.")
def test_server_auth(app: A2AStarletteApplication, handler: mock.AsyncMock):
    class TestAuthMiddleware(AuthenticationBackend):
        async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
            return (AuthCredentials(["authenticated"]), SimpleUser("test_user"))

    client = TestClient(app.build(middleware=[Middleware(AuthenticationMiddleware, backend=TestAuthMiddleware())]))
    handler.on_message_send.side_effect = lambda params, context: Message(
        context_id="session-xyz",
        message_id="112",
        role=Role.ROLE_AGENT,
        parts=[Part(text=context.user.user_name)],
    )
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "SendMessage",
            "params": {
                "message": {
                    "role": "ROLE_AGENT",
                    "parts": [{"text": "Hello"}],
                    "messageId": "111",
                    "taskId": "task1",
                    "contextId": "session-xyz",
                }
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["message"]["parts"][0]["text"] == "test_user"
    handler.on_message_send.assert_awaited_once()


# === STREAMING TESTS ===


async def test_message_send_stream(
    create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock, ensure_mock_task
) -> None:
    """Test streaming message sending."""

    async def stream_generator():
        for i in range(3):
            artifact = Artifact(
                artifact_id=f"artifact-{i}",
                name="result_data",
                parts=[TEXT_PART_DATA, DATA_PART],
            )
            last = [False, False, True]
            yield TaskArtifactUpdateEvent(
                artifact=artifact,
                task_id="task1",
                context_id="session-xyz",
                append=False,
                last_chunk=last[i],
            )

    handler.on_message_send_stream.return_value = stream_generator()

    client = None
    try:
        client = create_test_server(app.build())
        with client.stream(
            "POST",
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "123",
                "method": "SendStreamingMessage",
                "params": {
                    "message": {
                        "role": "ROLE_AGENT",
                        "parts": [{"text": "Hello"}],
                        "messageId": "111",
                        "taskId": "task1",
                        "contextId": "session-xyz",
                    }
                },
            },
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            content = b""
            event_count = 0
            for chunk in response.iter_bytes():
                content += chunk
                if b"data" in chunk:
                    event_count += 1

            assert b"artifact-0" in content
            assert b"artifact-1" in content
            assert b"artifact-2" in content
            assert event_count > 0
    finally:
        if client:
            client.close()
        await asyncio.sleep(0.1)


async def test_task_resubscription(
    create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock, ensure_mock_task
) -> None:
    """Test task resubscription streaming."""

    async def stream_generator():
        for i in range(3):
            artifact = Artifact(
                artifact_id=f"artifact-{i}",
                name="result_data",
                parts=[TEXT_PART_DATA, DATA_PART],
            )
            last = [False, False, True]
            yield TaskArtifactUpdateEvent(
                artifact=artifact,
                task_id="task1",
                context_id="session-xyz",
                append=False,
                last_chunk=last[i],
            )

    handler.on_subscribe_to_task.return_value = stream_generator()

    client = create_test_server(app.build())
    try:
        with client.stream(
            "POST",
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "123",
                "method": "SubscribeToTask",
                "params": {"id": "task1"},
            },
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            content = b""
            event_count = 0
            for chunk in response.iter_bytes():
                content += chunk
                if b"data:" in chunk:
                    event_count += 1

            assert b"artifact-0" in content
            assert b"artifact-1" in content
            assert b"artifact-2" in content
            assert event_count > 0
    finally:
        if client:
            client.close()
        await asyncio.sleep(0.1)


# === ERROR HANDLING TESTS ===


def test_invalid_json(client: Client):
    """Test handling invalid JSON."""
    response = client.post("/", content=b"This is not JSON")  # Use bytes
    assert response.status_code == 200  # JSON-RPC errors still return 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == JSONParseError().code


def test_invalid_request_structure(client: Client):
    """Test handling an invalid request structure."""
    response = client.post(
        "/",
        json={
            "jsonrpc": "aaaa",  # Missing or wrong required fields
            "id": "123",
            "method": "foo/bar",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    # The jsonrpc library returns MethodNotFoundError for unknown methods
    assert data["error"]["code"] == MethodNotFoundError().code


def test_method_not_implemented(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test handling MethodNotImplementedError."""
    handler.on_get_task.side_effect = UnsupportedOperationError()

    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "GetTask",
            "params": {"id": "task1"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32004  # UnsupportedOperationError


def test_unknown_method(client: Client):
    """Test handling unknown method."""
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "unknown/method",
            "params": {},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    # This should produce an UnsupportedOperationError error code
    assert data["error"]["code"] == MethodNotFoundError().code


def test_validation_error(client: Client):
    """Test handling validation error."""
    # Missing required fields in the message
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "SendMessage",
            "params": {
                "message": {
                    # Missing required fields
                    "text": "Hello"
                }
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == InvalidParamsError().code


def test_unhandled_exception(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test handling unhandled exception."""
    handler.on_get_task.side_effect = Exception("Unexpected error")

    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "GetTask",
            "params": {"id": "task1"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == InternalError().code
    assert "Unexpected error" in data["error"]["message"]


def test_get_method_to_rpc_endpoint(client: Client):
    """Test sending GET request to RPC endpoint."""
    response = client.get("/")
    # Should return 405 Method Not Allowed
    assert response.status_code == 405


def test_non_dict_json(client: Client):
    """Test handling JSON that's not a dict."""
    response = client.post("/", json=["not", "a", "dict"])
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == InvalidRequestError().code


# === DYNAMIC CARD MODIFIER TESTS ===


@pytest.mark.skip(reason="Dynamic card modifiers are not supported through the proxy.")
def test_dynamic_agent_card_modifier(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test that the card_modifier dynamically alters the public agent card."""

    async def modifier(card: AgentCard) -> AgentCard:
        modified_card = AgentCard()
        modified_card.CopyFrom(card)
        modified_card.name = "Dynamically Modified Agent"
        return modified_card

    app_instance = A2AStarletteApplication(agent_card, handler, card_modifier=modifier)
    client = TestClient(app_instance.build())

    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dynamically Modified Agent"
    assert data["version"] == agent_card.version  # Ensure other fields are intact


@pytest.mark.skip(reason="Dynamic card modifiers are not supported through the proxy.")
def test_dynamic_agent_card_modifier_sync(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test that a synchronous card_modifier dynamically alters the public agent card."""

    def modifier(card: AgentCard) -> AgentCard:
        modified_card = AgentCard()
        modified_card.CopyFrom(card)
        modified_card.name = "Dynamically Modified Agent"
        return modified_card

    app_instance = A2AStarletteApplication(agent_card, handler, card_modifier=modifier)
    client = TestClient(app_instance.build())

    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dynamically Modified Agent"
    assert data["version"] == agent_card.version  # Ensure other fields are intact


@pytest.mark.skip(reason="Dynamic card modifiers are not supported through the proxy.")
def test_dynamic_extended_agent_card_modifier(
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test that the extended_card_modifier dynamically alters the extended agent card."""
    agent_card.capabilities.extended_agent_card = True

    async def modifier(card: AgentCard, context: ServerCallContext) -> AgentCard:
        modified_card = AgentCard()
        modified_card.CopyFrom(card)
        modified_card.description = "Dynamically Modified Extended Description"
        return modified_card

    # Test with a base extended card
    app_instance = A2AStarletteApplication(
        agent_card,
        handler,
        extended_agent_card=extended_agent_card_fixture,
        extended_card_modifier=modifier,
    )
    client = TestClient(app_instance.build())

    response = client.get(EXTENDED_AGENT_CARD_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == extended_agent_card_fixture.name
    assert data["description"] == "Dynamically Modified Extended Description"

    # Test without a base extended card (modifier should receive public card)
    app_instance_no_base = A2AStarletteApplication(
        agent_card,
        handler,
        extended_agent_card=None,
        extended_card_modifier=modifier,
    )
    client_no_base = TestClient(app_instance_no_base.build())
    response_no_base = client_no_base.get(EXTENDED_AGENT_CARD_PATH)
    assert response_no_base.status_code == 200
    data_no_base = response_no_base.json()
    assert data_no_base["name"] == agent_card.name
    assert data_no_base["description"] == "Dynamically Modified Extended Description"


@pytest.mark.skip(reason="Dynamic card modifiers are not supported through the proxy.")
def test_dynamic_extended_agent_card_modifier_sync(
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test that a synchronous extended_card_modifier dynamically alters the extended agent card."""
    agent_card.capabilities.extended_agent_card = True

    def modifier(card: AgentCard, context: ServerCallContext) -> AgentCard:
        modified_card = AgentCard()
        modified_card.CopyFrom(card)
        modified_card.description = "Dynamically Modified Extended Description"
        return modified_card

    # Test with a base extended card
    app_instance = A2AStarletteApplication(
        agent_card,
        handler,
        extended_agent_card=extended_agent_card_fixture,
        extended_card_modifier=modifier,
    )
    client = TestClient(app_instance.build())

    response = client.get(EXTENDED_AGENT_CARD_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == extended_agent_card_fixture.name
    assert data["description"] == "Dynamically Modified Extended Description"

    # Test without a base extended card (modifier should receive public card)
    app_instance_no_base = A2AStarletteApplication(
        agent_card,
        handler,
        extended_agent_card=None,
        extended_card_modifier=modifier,
    )
    client_no_base = TestClient(app_instance_no_base.build())
    response_no_base = client_no_base.get(EXTENDED_AGENT_CARD_PATH)
    assert response_no_base.status_code == 200
    data_no_base = response_no_base.json()
    assert data_no_base["name"] == agent_card.name
    assert data_no_base["description"] == "Dynamically Modified Extended Description"


@pytest.mark.skip(reason="Dynamic card modifiers are not supported through the proxy.")
def test_fastapi_dynamic_agent_card_modifier(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test that the card_modifier dynamically alters the public agent card for FastAPI."""

    async def modifier(card: AgentCard) -> AgentCard:
        modified_card = AgentCard()
        modified_card.CopyFrom(card)
        modified_card.name = "Dynamically Modified Agent"
        return modified_card

    app_instance = A2AFastAPIApplication(agent_card, handler, card_modifier=modifier)
    client = TestClient(app_instance.build())

    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dynamically Modified Agent"


@pytest.mark.skip(reason="Dynamic card modifiers are not supported through the proxy.")
def test_fastapi_dynamic_agent_card_modifier_sync(agent_card: AgentCard, handler: mock.AsyncMock):
    """Test that a synchronous card_modifier dynamically alters the public agent card for FastAPI."""

    def modifier(card: AgentCard) -> AgentCard:
        modified_card = AgentCard()
        modified_card.CopyFrom(card)
        modified_card.name = "Dynamically Modified Agent"
        return modified_card

    app_instance = A2AFastAPIApplication(agent_card, handler, card_modifier=modifier)
    client = TestClient(app_instance.build())

    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dynamically Modified Agent"


# ------------------------------------- TESTS SPECIFIC TO PLATFORM PERMISSIONS -----------------------------------------


def test_task_ownership_different_user_cannot_access_task(
    create_test_server, handler: mock.AsyncMock, ensure_mock_task, test_user, test_admin
):
    """Test that a task owned by admin cannot be accessed by default user."""
    # Task is already created by ensure_mock_task for admin user

    # Setup mock response
    task_status = MINIMAL_TASK_STATUS
    task = Task(id="task1", context_id="ctx1", status=task_status)
    handler.on_get_task.return_value = task

    client = create_test_server()

    # Try to access as default user (without auth)
    client.auth = test_user
    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "123", "method": "GetTask", "params": {"id": "task1"}},
    )

    # Should fail with error (forbidden or not found)
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32001  # TaskNotFoundError

    # Now try as admin user (who owns it)
    client.auth = test_admin
    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "123", "method": "GetTask", "params": {"id": "task1"}},
    )

    # Should succeed
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["id"] == "task1"


async def test_unknown_task_raises_error(create_test_server, handler: mock.AsyncMock, db_transaction, test_admin):
    """Test that sending a message creates a new task owned by the user."""
    client = create_test_server()

    # Send message with non-existing task
    client.auth = test_admin
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "SendMessage",
            "params": {
                "message": {
                    "role": "ROLE_AGENT",
                    "parts": [{"text": "Hello"}],
                    "taskId": "unknown-task",
                    "messageId": "111",
                    "contextId": "session-xyz",
                }
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32001  # TaskNotFoundError


async def test_task_ownership_new_task_creation_via_message_send(
    create_test_server, handler: mock.AsyncMock, db_transaction, test_admin, test_user
):
    """Test that sending a message creates a new task owned by the user."""
    # Setup mock response - server returns a new task
    task_status = MINIMAL_TASK_STATUS
    mock_task = Task(
        id="new-task-123",
        context_id="session-xyz",
        status=task_status,
    )
    handler.on_message_send.return_value = mock_task

    client = create_test_server()

    # Send message as admin which should create new task ownership
    client.auth = test_admin
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "SendMessage",
            "params": {
                "message": {
                    "role": "ROLE_AGENT",
                    "parts": [{"text": "Hello"}],
                    "messageId": "111",
                    "contextId": "session-xyz",
                }
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["task"]["id"] == "new-task-123"

    # Verify task was recorded in database for admin user
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "new-task-123"},
    )
    row = result.fetchone()
    assert row is not None
    assert row.task_id == "new-task-123"

    # Verify we can access it as admin
    task = Task(id="new-task-123", context_id="ctx1", status=task_status)
    handler.on_get_task.return_value = task

    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "124", "method": "GetTask", "params": {"id": "new-task-123"}},
    )

    assert response.status_code == 200
    assert response.json()["result"]["id"] == "new-task-123"

    # Verify default user cannot access it
    client.auth = test_user
    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "125", "method": "GetTask", "params": {"id": "new-task-123"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32001  # TaskNotFoundError


async def test_context_ownership_cannot_be_claimed_by_different_user(
    create_test_server, handler: mock.AsyncMock, db_transaction, test_admin, test_user
):
    """Test that a context_id owned by one user cannot be used by another."""
    task_status = MINIMAL_TASK_STATUS

    client = create_test_server()

    # Admin creates a message with a specific context
    client.auth = test_admin
    mock_task = Task(id="task-ctx-1", context_id="shared-context-789", status=task_status)
    handler.on_message_send.return_value = mock_task

    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "SendMessage",
            "params": {
                "message": {
                    "role": "ROLE_AGENT",
                    "parts": [{"text": "Hello"}],
                    "messageId": "111",
                    "contextId": "shared-context-789",
                }
            },
        },
    )

    assert response.status_code == 200

    # Verify context was recorded for admin
    context_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "shared-context-789"},
    )
    context_row = context_result.fetchone()
    assert context_row is not None

    # Now default user tries to use the same context - should fail
    client.auth = test_user
    mock_task2 = Task(
        id="task-ctx-2",
        context_id="shared-context-789",  # Same context!
        status=task_status,
    )
    handler.on_message_send.return_value = mock_task2

    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "124",
            "method": "SendMessage",
            "params": {
                "message": {
                    "role": "ROLE_AGENT",
                    "parts": [{"text": "Hello"}],
                    "messageId": "112",
                    "contextId": "shared-context-789",
                }
            },
        },
    )

    # Should fail
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == InvalidRequestError().code
    assert "insufficient permissions" in data["error"]["message"].lower()


async def test_task_update_last_accessed_at(create_test_server, handler: mock.AsyncMock, db_transaction, test_admin):
    """Test that accessing a task updates last_accessed_at timestamp."""
    client = create_test_server()
    client.auth = test_admin

    mock_task = Task(
        id="task1", context_id="shared-context-789", status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED)
    )
    handler.on_message_send.return_value = mock_task
    message_data = {
        "jsonrpc": "2.0",
        "id": "123",
        "method": "SendMessage",
        "params": {
            "message": {
                "role": "ROLE_AGENT",
                "parts": [{"text": "Hello"}],
                "messageId": "111",
                "contextId": "shared-context-789",
            }
        },
    }

    response = client.post("/", json=message_data)
    # Get initial timestamp
    result = await db_transaction.execute(
        text("SELECT last_accessed_at FROM a2a_request_tasks WHERE task_id = :task_id"), {"task_id": "task1"}
    )
    initial_timestamp = result.fetchone().last_accessed_at

    # Wait a bit to ensure timestamp difference
    await asyncio.sleep(0.1)

    # Access the task
    task_status = MINIMAL_TASK_STATUS
    task = Task(id="task1", context_id="ctx1", status=task_status)
    handler.on_get_task.return_value = task

    response = client.post("/", json=message_data)
    assert response.status_code == 200

    # Check that timestamp was updated
    result = await db_transaction.execute(
        text("SELECT last_accessed_at FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "task1"},
    )
    new_timestamp = result.fetchone().last_accessed_at
    assert new_timestamp > initial_timestamp


async def test_task_and_context_both_specified_single_query(
    create_test_server, handler: mock.AsyncMock, db_transaction, test_admin
):
    """Test that both task_id and context_id are tracked in a single query when both are specified."""
    client = create_test_server()
    client.auth = test_admin

    task_status = MINIMAL_TASK_STATUS
    mock_task = Task(id="dual-task-123", context_id="dual-context-456", status=task_status)
    handler.on_message_send.return_value = mock_task

    message_data = {
        "jsonrpc": "2.0",
        "id": "123",
        "method": "SendMessage",
        "params": {
            "message": {
                "role": "ROLE_AGENT",
                "parts": [{"text": "Hello"}],
                "messageId": "111",
                "contextId": "dual-context-456",
            }
        },
    }
    response = client.post("/", json=message_data)
    assert response.status_code == 200
    message_data["params"]["message"]["taskId"] = "dual-task-123"

    response = client.post("/", json=message_data)
    assert response.status_code == 200

    # Verify both were recorded in database
    task_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "dual-task-123"},
    )
    assert task_result.fetchone() is not None

    context_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "dual-context-456"},
    )
    assert context_result.fetchone() is not None


async def test_invalid_request_raises_a2a_error(create_test_server, handler: mock.AsyncMock, db_transaction):
    """Test that an invalid request to an offline provider returns an A2A error."""

    client = create_test_server()

    # set provider as offline
    provider_id = str(client.base_url).rstrip("/").split("/")[-1]
    await db_transaction.execute(
        text("UPDATE providers SET unmanaged_state = 'offline' WHERE id = :provider_id"),
        {"provider_id": provider_id},
    )
    await db_transaction.commit()

    message_data = {
        "jsonrpc": "2.0",
        "id": "123",
        "method": "SendMessage",
        "params": {
            "message": {
                "role": "ROLE_AGENT",
                "parts": [{"text": "Hello"}],
                "messageId": "111",
            }
        },
    }
    response = client.post("/", json=message_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "123"
    assert "error" in data
    assert data["error"]["code"] == InvalidRequestError().code
    assert "provider is offline" in data["error"]["message"]
