# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# Testing proxy server capabilities, using tests from a2a:
# https://github.com/a2aproject/a2a-python/blob/main/tests/server/test_integration.py
import asyncio
import contextlib
import socket
import time
import uuid
from contextlib import closing
from threading import Thread
from typing import Any
from unittest import mock

import pytest
import uvicorn
from a2a.server.apps import (
    A2AFastAPIApplication,
    A2AStarletteApplication,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    Artifact,
    DataPart,
    InternalError,
    InvalidParamsError,
    InvalidRequestError,
    JSONParseError,
    Message,
    MethodNotFoundError,
    Part,
    PushNotificationConfig,
    Role,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskState,
    TaskStatus,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from a2a.utils.errors import MethodNotImplementedError
from fastapi import FastAPI
from httpx import Client
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

from agentstack_server.infrastructure.persistence.repositories.user import users_table

pytestmark = pytest.mark.e2e

# === TEST SETUP ===

MINIMAL_AGENT_SKILL: dict[str, Any] = {
    "id": "skill-123",
    "name": "Recipe Finder",
    "description": "Finds recipes",
    "tags": ["cooking"],
}

MINIMAL_AGENT_AUTH: dict[str, Any] = {"schemes": ["Bearer"]}

AGENT_CAPS = AgentCapabilities(pushNotifications=True, stateTransitionHistory=False, streaming=True)

MINIMAL_AGENT_CARD: dict[str, Any] = {
    "authentication": MINIMAL_AGENT_AUTH,
    "capabilities": AGENT_CAPS,  # AgentCapabilities is required but can be empty
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["application/json"],
    "description": "Test Agent",
    "name": "TestAgent",
    "skills": [MINIMAL_AGENT_SKILL],
    "url": "http://example.com/agent",
    "version": "1.0",
}

EXTENDED_AGENT_CARD_DATA: dict[str, Any] = {
    **MINIMAL_AGENT_CARD,
    "name": "TestAgent Extended",
    "description": "Test Agent with more details",
    "skills": [
        MINIMAL_AGENT_SKILL,
        {
            "id": "skill-extended",
            "name": "Extended Skill",
            "description": "Does more things",
            "tags": ["extended"],
        },
    ],
}
TEXT_PART_DATA: dict[str, Any] = {"kind": "text", "text": "Hello"}

DATA_PART_DATA: dict[str, Any] = {"kind": "data", "data": {"key": "value"}}

MINIMAL_MESSAGE_USER: dict[str, Any] = {
    "role": "user",
    "parts": [TEXT_PART_DATA],
    "messageId": "msg-123",
    "kind": "message",
}

MINIMAL_TASK_STATUS: dict[str, Any] = {"state": "submitted"}

FULL_TASK_STATUS: dict[str, Any] = {
    "state": "working",
    "message": MINIMAL_MESSAGE_USER,
    "timestamp": "2023-10-27T10:00:00Z",
}


@pytest.fixture
def agent_card():
    return AgentCard(**MINIMAL_AGENT_CARD)


@pytest.fixture
def extended_agent_card_fixture():
    return AgentCard(**EXTENDED_AGENT_CARD_DATA)


@pytest.fixture
def handler():
    handler = mock.AsyncMock()
    handler.on_message_send = mock.AsyncMock()
    handler.on_cancel_task = mock.AsyncMock()
    handler.on_get_task = mock.AsyncMock()
    handler.set_push_notification = mock.AsyncMock()
    handler.get_push_notification = mock.AsyncMock()
    handler.on_message_send_stream = mock.Mock()
    handler.on_resubscribe_to_task = mock.Mock()
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
def create_test_server(free_port: int, app: A2AStarletteApplication, test_configuration, clean_up_fn):
    server_instance: uvicorn.Server | None = None
    thread: Thread | None = None
    app.agent_card.url = f"http://host.docker.internal:{free_port}"

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

        with Client(base_url=f"{test_configuration.server_url}/api/v1", auth=("admin", "test-password")) as client:
            for _attempt in range(20):
                resp = client.post(
                    "providers",
                    json={"location": f"http://host.docker.internal:{free_port}"},
                    timeout=1,
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
            base_url=f"{test_configuration.server_url}/api/v1/a2a/{provider_id}",
            auth=("admin", "test-password"),
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
@pytest.mark.usefixtures("clean_up")
async def ensure_mock_task(db_transaction):
    res = await db_transaction.execute(users_table.select().where(users_table.c.email == "admin@beeai.dev"))
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
def client(create_test_server, test_configuration):
    """Create a test client with the Starlette app."""
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


def test_authenticated_extended_agent_card_endpoint_not_supported(
    create_test_server, agent_card: AgentCard, handler: mock.AsyncMock
):
    """Test extended card endpoint returns 404 if not supported by main card."""
    # Ensure supportsAuthenticatedExtendedCard is False or None
    agent_card.supports_authenticated_extended_card = False
    app_instance = A2AStarletteApplication(agent_card, handler)
    # The route should not even be added if supportsAuthenticatedExtendedCard is false
    # So, building the app and trying to hit it should result in 404 from Starlette itself
    client = create_test_server(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 404  # Starlette's default for no route


def test_authenticated_extended_agent_card_endpoint_not_supported_fastapi(
    create_test_server, agent_card: AgentCard, handler: mock.AsyncMock
):
    """Test extended card endpoint returns 404 if not supported by main card."""
    # Ensure supportsAuthenticatedExtendedCard is False or None
    agent_card.supports_authenticated_extended_card = False
    app_instance = A2AFastAPIApplication(agent_card, handler)
    # The route should not even be added if supportsAuthenticatedExtendedCard is false
    # So, building the app and trying to hit it should result in 404 from FastAPI itself
    client = create_test_server(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 404  # FastAPI's default for no route


@pytest.mark.skip(reason="Extended agent card is not supported at the moment. # TODO")
def test_authenticated_extended_agent_card_endpoint_supported_with_specific_extended_card_starlette(
    create_test_server,
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test extended card endpoint returns the specific extended card when provided."""
    agent_card.supports_authenticated_extended_card = True  # Main card must support it
    print(agent_card)
    app_instance = A2AStarletteApplication(agent_card, handler, extended_agent_card=extended_agent_card_fixture)
    client = create_test_server(app_instance.build())

    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 200
    data = response.json()
    # Verify it's the extended card's data
    assert data["name"] == extended_agent_card_fixture.name
    assert data["version"] == extended_agent_card_fixture.version
    assert len(data["skills"]) == len(extended_agent_card_fixture.skills)
    assert any(skill["id"] == "skill-extended" for skill in data["skills"]), "Extended skill not found in served card"


@pytest.mark.skip(reason="Extended agent card is not supported at the moment. # TODO")
def test_authenticated_extended_agent_card_endpoint_supported_with_specific_extended_card_fastapi(
    create_test_server,
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test extended card endpoint returns the specific extended card when provided."""
    agent_card.supports_authenticated_extended_card = True  # Main card must support it
    app_instance = A2AFastAPIApplication(agent_card, handler, extended_agent_card=extended_agent_card_fixture)
    client = create_test_server(app_instance.build())

    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 200
    data = response.json()
    # Verify it's the extended card's data
    assert data["name"] == extended_agent_card_fixture.name
    assert data["version"] == extended_agent_card_fixture.version
    assert len(data["skills"]) == len(extended_agent_card_fixture.skills)
    assert any(skill["id"] == "skill-extended" for skill in data["skills"]), "Extended skill not found in served card"


@pytest.mark.skip(reason="Custom agent card urls are not supported at the moment.")
def test_agent_card_custom_url(create_test_server, app: A2AStarletteApplication, agent_card: AgentCard):
    """Test the agent card endpoint with a custom URL."""
    client = create_test_server(app.build(agent_card_url="/my-agent"))
    response = client.get("/my-agent")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


@pytest.mark.skip(reason="Custom RPC urls are not supported at the moment.")
def test_starlette_rpc_endpoint_custom_url(
    create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock, ensure_mock_task
):
    """Test the RPC endpoint with a custom URL."""
    # Provide a valid Task object as the return value
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", context_id="ctx1", state="completed", status=task_status)
    handler.on_get_task.return_value = task
    client = create_test_server(app.build(rpc_url="/api/rpc"))
    response = client.post(
        "/api/rpc",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tasks/get",
            "params": {"id": "task1"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["id"] == "task1"


@pytest.mark.skip(reason="Custom RPC urls are not supported at the moment.")
def test_fastapi_rpc_endpoint_custom_url(create_test_server, app: A2AFastAPIApplication, handler: mock.AsyncMock):
    """Test the RPC endpoint with a custom URL."""
    # Provide a valid Task object as the return value
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", context_id="ctx1", state="completed", status=task_status)
    handler.on_get_task.return_value = task
    client = create_test_server(app.build(rpc_url="/api/rpc"))
    response = client.post(
        "/api/rpc",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tasks/get",
            "params": {"id": "task1"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["id"] == "task1"


@pytest.mark.skip(reason="Custom routes are not supported by the proxy.")
def test_starlette_build_with_extra_routes(create_test_server, app: A2AStarletteApplication, agent_card: AgentCard):
    """Test building the app with additional routes."""

    def custom_handler(request):
        return JSONResponse({"message": "Hello"})

    extra_route = Route("/hello", custom_handler, methods=["GET"])
    test_app = app.build(routes=[extra_route])
    client = create_test_server(test_app)

    # Test the added route
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

    # Ensure default routes still work
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


@pytest.mark.skip(reason="Custom routes are not supported by the proxy.")
def test_fastapi_build_with_extra_routes(create_test_server, app: A2AFastAPIApplication, agent_card: AgentCard):
    """Test building the app with additional routes."""

    def custom_handler(request):
        return JSONResponse({"message": "Hello"})

    extra_route = Route("/hello", custom_handler, methods=["GET"])
    test_app = app.build(routes=[extra_route])
    client = create_test_server(test_app)

    # Test the added route
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

    # Ensure default routes still work
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


# === REQUEST METHODS TESTS ===


def test_send_message(create_test_server, handler: mock.AsyncMock, agent_card, ensure_mock_task):
    """Test sending a message."""
    # Prepare mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    mock_task = Task(
        id="task1",
        context_id="session-xyz",
        status=task_status,
    )
    handler.on_message_send.return_value = mock_task

    # Send request
    app_instance = A2AStarletteApplication(agent_card, handler)
    client = create_test_server(app_instance.build())
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "agent",
                    "parts": [{"kind": "text", "text": "Hello"}],
                    "messageId": "111",
                    "kind": "message",
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
    assert data["result"]["id"] == "task1"
    assert data["result"]["status"]["state"] == "submitted"

    # Verify handler was called
    handler.on_message_send.assert_awaited_once()


async def test_cancel_task(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test cancelling a task."""
    # Setup mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task_status.state = TaskState.canceled  # 'cancelled' #
    task = Task(id="task1", context_id="ctx1", state="cancelled", status=task_status)
    handler.on_cancel_task.return_value = task

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tasks/cancel",
            "params": {"id": "task1"},
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["id"] == "task1"
    assert data["result"]["status"]["state"] == "canceled"

    # Verify handler was called
    handler.on_cancel_task.assert_awaited_once()


async def test_get_task(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test getting a task."""
    # Setup mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", context_id="ctx1", state="completed", status=task_status)
    handler.on_get_task.return_value = task  # JSONRPCResponse(root=task)

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tasks/get",
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
        task_id="task1",
        push_notification_config=PushNotificationConfig(url="https://example.com", token="secret-token"),
    )
    handler.on_set_task_push_notification_config.return_value = task_push_config

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tasks/pushNotificationConfig/set",
            "params": {
                "taskId": "task1",
                "pushNotificationConfig": {
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
    handler.on_set_task_push_notification_config.assert_awaited_once()


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
            "method": "tasks/pushNotificationConfig/get",
            "params": {"id": "task1"},
        },
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["pushNotificationConfig"]["token"] == "secret-token"

    # Verify handler was called
    handler.on_get_task_push_notification_config.assert_awaited_once()


def test_server_auth(create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock, ensure_mock_task):
    class TestAuthMiddleware(AuthenticationBackend):
        async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
            # For the purposes of this test, all requests are authenticated!
            return (AuthCredentials(["authenticated"]), SimpleUser("test_user"))

    client = create_test_server(
        app.build(middleware=[Middleware(AuthenticationMiddleware, backend=TestAuthMiddleware())])
    )

    # Set the output message to be the authenticated user name
    handler.on_message_send.side_effect = lambda params, context: Message(
        context_id="session-xyz",
        message_id="112",
        role=Role.agent,
        parts=[
            Part(TextPart(text=context.user.user_name)),
        ],
    )

    # Send request
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "agent",
                    "parts": [{"kind": "text", "text": "Hello"}],
                    "messageId": "111",
                    "kind": "message",
                    "taskId": "task1",
                    "contextId": "session-xyz",
                }
            },
        },
    )

    # Verify response
    assert response.status_code == 200
    result = SendMessageResponse.model_validate(response.json())
    assert isinstance(result.root, SendMessageSuccessResponse)
    assert isinstance(result.root.result, Message)
    message = result.root.result
    assert isinstance(message.parts[0].root, TextPart)
    assert message.parts[0].root.text == "test_user"

    # Verify handler was called
    handler.on_message_send.assert_awaited_once()


# === STREAMING TESTS ===


async def test_message_send_stream(
    create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock, ensure_mock_task
) -> None:
    """Test streaming message sending."""

    # Setup mock streaming response
    async def stream_generator():
        for i in range(3):
            text_part = TextPart(**TEXT_PART_DATA)
            data_part = DataPart(**DATA_PART_DATA)
            artifact = Artifact(
                artifact_id=f"artifact-{i}",
                name="result_data",
                parts=[Part(root=text_part), Part(root=data_part)],
            )
            last = [False, False, True]
            task_artifact_update_event_data: dict[str, Any] = {
                "artifact": artifact,
                "taskId": "task1",
                "contextId": "session-xyz",
                "append": False,
                "lastChunk": last[i],
                "kind": "artifact-update",
            }

            yield TaskArtifactUpdateEvent.model_validate(task_artifact_update_event_data)

    handler.on_message_send_stream.return_value = stream_generator()

    client = None
    try:
        # Create client
        client = create_test_server(app.build())
        # Send request
        with client.stream(
            "POST",
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "123",
                "method": "message/stream",
                "params": {
                    "message": {
                        "role": "agent",
                        "parts": [{"kind": "text", "text": "Hello"}],
                        "messageId": "111",
                        "kind": "message",
                        "taskId": "task1",
                        "contextId": "session-xyz",
                    }
                },
            },
        ) as response:
            # Verify response is a stream
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            # Read some content to verify streaming works
            content = b""
            event_count = 0

            for chunk in response.iter_bytes():
                content += chunk
                if b"data" in chunk:  # Naive check for SSE data lines
                    event_count += 1

            # Check content has event data (e.g., part of the first event)
            assert b'"artifactId":"artifact-0"' in content  # Check for the actual JSON payload
            assert b'"artifactId":"artifact-1"' in content  # Check for the actual JSON payload
            assert b'"artifactId":"artifact-2"' in content  # Check for the actual JSON payload
            assert event_count > 0
    finally:
        # Ensure the client is closed
        if client:
            client.close()
        # Allow event loop to process any pending callbacks
        await asyncio.sleep(0.1)


async def test_task_resubscription(
    create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock, ensure_mock_task
) -> None:
    """Test task resubscription streaming."""

    # Setup mock streaming response
    async def stream_generator():
        for i in range(3):
            text_part = TextPart(**TEXT_PART_DATA)
            data_part = DataPart(**DATA_PART_DATA)
            artifact = Artifact(
                artifact_id=f"artifact-{i}",
                name="result_data",
                parts=[Part(root=text_part), Part(root=data_part)],
            )
            last = [False, False, True]
            task_artifact_update_event_data: dict[str, Any] = {
                "artifact": artifact,
                "taskId": "task1",
                "contextId": "session-xyz",
                "append": False,
                "lastChunk": last[i],
                "kind": "artifact-update",
            }
            yield TaskArtifactUpdateEvent.model_validate(task_artifact_update_event_data)

    handler.on_resubscribe_to_task.return_value = stream_generator()

    # Create client
    client = create_test_server(app.build())

    try:
        # Send request using client.stream() context manager
        # Send request
        with client.stream(
            "POST",
            "/",
            json={
                "jsonrpc": "2.0",
                "id": "123",  # This ID is used in the success_event above
                "method": "tasks/resubscribe",
                "params": {"id": "task1"},
            },
        ) as response:
            # Verify response is a stream
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Read some content to verify streaming works
            content = b""
            event_count = 0
            for chunk in response.iter_bytes():
                content += chunk
                # A more robust check would be to parse each SSE event
                if b"data:" in chunk:  # Naive check for SSE data lines
                    event_count += 1

                # TODO: WTF? processing just first event but checking all 3?
                # if event_count >= 1 and len(content) > 20:  # Ensure we've processed at least one event
                #     break

            # Check content has event data (e.g., part of the first event)
            assert b'"artifactId":"artifact-0"' in content  # Check for the actual JSON payload
            assert b'"artifactId":"artifact-1"' in content  # Check for the actual JSON payload
            assert b'"artifactId":"artifact-2"' in content  # Check for the actual JSON payload
            assert event_count > 0
    finally:
        # Ensure the client is closed
        if client:
            client.close()
        # Allow event loop to process any pending callbacks
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
            # Missing required fields
            "id": "123"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == InvalidRequestError().code


def test_method_not_implemented(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test handling MethodNotImplementedError."""
    handler.on_get_task.side_effect = MethodNotImplementedError()

    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tasks/get",
            "params": {"id": "task1"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == UnsupportedOperationError().code


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
            "method": "message/send",
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
            "method": "tasks/get",
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


# ------------------------------------- TESTS SPECIFIC TO PLATFORM PERMISSIONS -----------------------------------------


def test_task_ownership_different_user_cannot_access_task(client: Client, handler: mock.AsyncMock, ensure_mock_task):
    """Test that a task owned by admin cannot be accessed by default user."""
    # Task is already created by ensure_mock_task for admin user

    # Setup mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", context_id="ctx1", state="completed", status=task_status)
    handler.on_get_task.return_value = task

    # Try to access as default user (without auth)
    client.auth = None
    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "123", "method": "tasks/get", "params": {"id": "task1"}},
    )

    # Should fail with error (forbidden or not found)
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] in [TaskNotFoundError().code]

    # Now try as admin user (who owns it)
    client.auth = ("admin", "test-password")
    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "123", "method": "tasks/get", "params": {"id": "task1"}},
    )

    # Should succeed
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["id"] == "task1"


async def test_task_ownership_new_task_creation_via_message_send(
    client: Client, handler: mock.AsyncMock, db_transaction
):
    """Test that sending a message creates a new task owned by the user."""
    # Setup mock response - server returns a new task
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    mock_task = Task(
        id="new-task-123",
        context_id="session-xyz",
        status=task_status,
    )
    handler.on_message_send.return_value = mock_task

    # Send message as admin which should create new task ownership
    client.auth = ("admin", "test-password")
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "agent",
                    "parts": [{"kind": "text", "text": "Hello"}],
                    "messageId": "111",
                    "kind": "message",
                    "contextId": "session-xyz",
                }
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["id"] == "new-task-123"

    # Verify task was recorded in database for admin user
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "new-task-123"},
    )
    row = result.fetchone()
    assert row is not None
    assert row.task_id == "new-task-123"

    # Verify we can access it as admin
    task = Task(id="new-task-123", context_id="ctx1", state="completed", status=task_status)
    handler.on_get_task.return_value = task

    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "124", "method": "tasks/get", "params": {"id": "new-task-123"}},
    )

    assert response.status_code == 200
    assert response.json()["result"]["id"] == "new-task-123"

    # Verify default user cannot access it
    client.auth = None
    response = client.post(
        "/",
        json={"jsonrpc": "2.0", "id": "125", "method": "tasks/get", "params": {"id": "new-task-123"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] in [TaskNotFoundError().code]


async def test_context_ownership_cannot_be_claimed_by_different_user(
    client: Client, handler: mock.AsyncMock, db_transaction
):
    """Test that a context_id owned by one user cannot be used by another."""
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)

    # Admin creates a message with a specific context
    client.auth = ("admin", "test-password")
    mock_task = Task(id="task-ctx-1", context_id="shared-context-789", status=task_status)
    handler.on_message_send.return_value = mock_task

    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "agent",
                    "parts": [{"kind": "text", "text": "Hello"}],
                    "messageId": "111",
                    "kind": "message",
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
    client.auth = None
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
            "method": "message/send",
            "params": {
                "message": {
                    "role": "agent",
                    "parts": [{"kind": "text", "text": "Hello"}],
                    "messageId": "112",
                    "kind": "message",
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


async def test_task_update_last_accessed_at(client: Client, handler: mock.AsyncMock, db_transaction):
    """Test that accessing a task updates last_accessed_at timestamp."""
    client.auth = ("admin", "test-password")

    mock_task = Task(id="task1", context_id="shared-context-789", status=TaskStatus(state=TaskState.submitted))
    handler.on_message_send.return_value = mock_task
    message_data = {
        "jsonrpc": "2.0",
        "id": "123",
        "method": "message/send",
        "params": {
            "message": {
                "role": "agent",
                "parts": [{"kind": "text", "text": "Hello"}],
                "messageId": "111",
                "kind": "message",
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
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", context_id="ctx1", state="completed", status=task_status)
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


async def test_task_and_context_both_specified_single_query(client: Client, handler: mock.AsyncMock, db_transaction):
    """Test that both task_id and context_id are tracked in a single query when both are specified."""
    client.auth = ("admin", "test-password")

    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    mock_task = Task(id="dual-task-123", context_id="dual-context-456", status=task_status)
    handler.on_message_send.return_value = mock_task

    message_data = {
        "jsonrpc": "2.0",
        "id": "123",
        "method": "message/send",
        "params": {
            "message": {
                "role": "agent",
                "parts": [{"kind": "text", "text": "Hello"}],
                "messageId": "111",
                "kind": "message",
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
