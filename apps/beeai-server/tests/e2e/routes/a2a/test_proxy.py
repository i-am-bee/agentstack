# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# Testing proxy server capabilities, using tests from a2a:
# https://github.com/a2aproject/a2a-python/blob/main/tests/server/test_integration.py
import asyncio
import contextlib
import socket
import time
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
    InvalidRequestError,
    JSONParseError,
    Message,
    Part,
    PushNotificationConfig,
    Role,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskPushNotificationConfig,
    TaskState,
    TaskStatus,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import MethodNotImplementedError
from fastapi import FastAPI
from httpx import Client
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

        with Client(base_url=f"{test_configuration.server_url}/api/v1") as client:
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
                raise RuntimeError("Server did not start or register itself correctly")

        return Client(base_url=f"{test_configuration.server_url}/api/v1/a2a/{provider_id}")

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
def client(create_test_server, test_configuration):
    """Create a test client with the Starlette app."""
    return create_test_server()


# === BASIC FUNCTIONALITY TESTS ===


def test_agent_card_endpoint(client: Client, agent_card: AgentCard):
    """Test the agent card endpoint returns expected data."""
    response = client.get("/.well-known/agent.json")
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
    agent_card.supportsAuthenticatedExtendedCard = False
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
    agent_card.supportsAuthenticatedExtendedCard = False
    app_instance = A2AFastAPIApplication(agent_card, handler)
    # The route should not even be added if supportsAuthenticatedExtendedCard is false
    # So, building the app and trying to hit it should result in 404 from FastAPI itself
    client = create_test_server(app_instance.build())
    response = client.get("/agent/authenticatedExtendedCard")
    assert response.status_code == 404  # FastAPI's default for no route


def test_authenticated_extended_agent_card_endpoint_supported_with_specific_extended_card_starlette(
    create_test_server,
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test extended card endpoint returns the specific extended card when provided."""
    agent_card.supportsAuthenticatedExtendedCard = True  # Main card must support it
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


def test_authenticated_extended_agent_card_endpoint_supported_with_specific_extended_card_fastapi(
    create_test_server,
    agent_card: AgentCard,
    extended_agent_card_fixture: AgentCard,
    handler: mock.AsyncMock,
):
    """Test extended card endpoint returns the specific extended card when provided."""
    agent_card.supportsAuthenticatedExtendedCard = True  # Main card must support it
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


def test_agent_card_custom_url(create_test_server, app: A2AStarletteApplication, agent_card: AgentCard):
    """Test the agent card endpoint with a custom URL."""
    client = create_test_server(app.build(agent_card_url="/my-agent"))
    response = client.get("/my-agent")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


def test_starlette_rpc_endpoint_custom_url(create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock):
    """Test the RPC endpoint with a custom URL."""
    # Provide a valid Task object as the return value
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", contextId="ctx1", state="completed", status=task_status)
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


def test_fastapi_rpc_endpoint_custom_url(create_test_server, app: A2AFastAPIApplication, handler: mock.AsyncMock):
    """Test the RPC endpoint with a custom URL."""
    # Provide a valid Task object as the return value
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", contextId="ctx1", state="completed", status=task_status)
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
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


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
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_card.name


# === REQUEST METHODS TESTS ===


def test_send_message(create_test_server, handler: mock.AsyncMock, agent_card):
    """Test sending a message."""
    # Prepare mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    mock_task = Task(
        id="task1",
        contextId="session-xyz",
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


def test_cancel_task(client: Client, handler: mock.AsyncMock):
    """Test cancelling a task."""
    # Setup mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task_status.state = TaskState.canceled  # 'cancelled' #
    task = Task(id="task1", contextId="ctx1", state="cancelled", status=task_status)
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


def test_get_task(client: Client, handler: mock.AsyncMock):
    """Test getting a task."""
    # Setup mock response
    task_status = TaskStatus(**MINIMAL_TASK_STATUS)
    task = Task(id="task1", contextId="ctx1", state="completed", status=task_status)
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


def test_set_push_notification_config(client: Client, handler: mock.AsyncMock):
    """Test setting push notification configuration."""
    # Setup mock response
    task_push_config = TaskPushNotificationConfig(
        taskId="t2",
        pushNotificationConfig=PushNotificationConfig(url="https://example.com", token="secret-token"),
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
                "taskId": "t2",
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


def test_get_push_notification_config(client: Client, handler: mock.AsyncMock):
    """Test getting push notification configuration."""
    # Setup mock response
    task_push_config = TaskPushNotificationConfig(
        taskId="task1",
        pushNotificationConfig=PushNotificationConfig(url="https://example.com", token="secret-token"),
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


def test_server_auth(create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock):
    class TestAuthMiddleware(AuthenticationBackend):
        async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
            # For the purposes of this test, all requests are authenticated!
            return (AuthCredentials(["authenticated"]), SimpleUser("test_user"))

    client = create_test_server(
        app.build(middleware=[Middleware(AuthenticationMiddleware, backend=TestAuthMiddleware())])
    )

    # Set the output message to be the authenticated user name
    handler.on_message_send.side_effect = lambda params, context: Message(
        contextId="session-xyz",
        messageId="112",
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


@pytest.mark.asyncio
async def test_message_send_stream(create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock) -> None:
    """Test streaming message sending."""

    # Setup mock streaming response
    async def stream_generator():
        for i in range(3):
            text_part = TextPart(**TEXT_PART_DATA)
            data_part = DataPart(**DATA_PART_DATA)
            artifact = Artifact(
                artifactId=f"artifact-{i}",
                name="result_data",
                parts=[Part(root=text_part), Part(root=data_part)],
            )
            last = [False, False, True]
            task_artifact_update_event_data: dict[str, Any] = {
                "artifact": artifact,
                "taskId": "task_id",
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
                        "taskId": "taskId",
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


@pytest.mark.asyncio
async def test_task_resubscription(create_test_server, app: A2AStarletteApplication, handler: mock.AsyncMock) -> None:
    """Test task resubscription streaming."""

    # Setup mock streaming response
    async def stream_generator():
        for i in range(3):
            text_part = TextPart(**TEXT_PART_DATA)
            data_part = DataPart(**DATA_PART_DATA)
            artifact = Artifact(
                artifactId=f"artifact-{i}",
                name="result_data",
                parts=[Part(root=text_part), Part(root=data_part)],
            )
            last = [False, False, True]
            task_artifact_update_event_data: dict[str, Any] = {
                "artifact": artifact,
                "taskId": "task_id",
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


def test_method_not_implemented(client: Client, handler: mock.AsyncMock):
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
    assert data["error"]["code"] == InvalidRequestError().code


def test_validation_error(client: Client):
    """Test handling validation error."""
    # Missing required fields in the message
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "123",
            "method": "messages/send",
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
    assert data["error"]["code"] == InvalidRequestError().code


def test_unhandled_exception(client: Client, handler: mock.AsyncMock):
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
