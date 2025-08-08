# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from a2a.client import A2AClient, create_text_message_object
from a2a.types import (
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext


def create_send_request_object(text: str | None = None, task_id: str | None = None):
    message = create_text_message_object(content=text or "test")
    if task_id:
        message.task_id = task_id
    return SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )


def create_streaming_request_object(text: str | None = None, task_id: str | None = None):
    message = create_text_message_object(content=text or "test")
    if task_id:
        message.task_id = task_id
    return SendStreamingMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )


@pytest.fixture
async def sync_function_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    def sync_function_agent(message: Message):
        """Synchronous function agent that returns a string directly."""
        return f"sync_function_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(sync_function_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_function_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    def sync_function_with_context_agent(message: Message, context: RunContext):
        """Synchronous function agent with context that uses context.yield_sync."""
        context.yield_sync("first sync yield")
        return f"sync_function_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(sync_function_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_generator_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    def sync_generator_agent(message: Message):
        """Synchronous generator agent that uses yield statements."""
        yield "sync_generator yield 1"
        yield "sync_generator yield 2"

    async with create_server_with_agent(sync_generator_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_generator_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    def sync_generator_with_context_agent(message: Message, context: RunContext):
        """Synchronous generator agent with context using both yields and context.yield_sync."""
        yield "sync_generator_with_context yield 1"
        context.yield_sync("sync_generator_with_context context yield")
        yield "sync_generator_with_context yield 2"
        yield f"sync_generator_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(sync_generator_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def async_function_agent(message: Message):
        """Asynchronous function agent that returns a string directly."""
        await asyncio.sleep(0.01)
        return f"async_function_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_function_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def async_function_with_context_agent(message: Message, context: RunContext):
        """Asynchronous function agent with context that uses context.yield_async."""
        await context.yield_async("first async yield")
        await asyncio.sleep(0.01)
        return f"async_function_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_function_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def async_generator_agent(message: Message):
        """Asynchronous generator agent that uses yield statements."""
        yield "async_generator yield 1"
        await asyncio.sleep(0.01)
        yield "async_generator yield 2"
        yield f"async_generator_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_generator_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def async_generator_with_context_agent(message: Message, context: RunContext):
        """Asynchronous generator agent with context using both yields and context.yield_async."""
        yield "async_generator_with_context yield 1"
        await context.yield_async("async_generator_with_context context yield")
        await asyncio.sleep(0.01)
        yield "async_generator_with_context yield 2"
        yield f"async_generator_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_generator_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_function_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    def sync_function_resume_agent(message: Message, context: RunContext):
        """Synchronous function agent that requires input and handles resume."""
        resume_message = context.yield_sync(
            TaskStatus(
                state=TaskState.input_required,
                message=create_text_message_object(content="Need input"),
            )
        )
        return f"sync_function_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(sync_function_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_generator_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    def sync_generator_resume_agent(message: Message, context: RunContext):
        """Synchronous generator agent that requires input and handles resume."""
        yield "sync_generator_resume_agent: starting"
        resume_message = yield TaskStatus(
            state=TaskState.input_required, message=create_text_message_object(content="Need input")
        )
        yield f"sync_generator_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(sync_generator_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def async_function_resume_agent(message: Message, context: RunContext):
        """Asynchronous function agent that requires input and handles resume."""
        resume_message = await context.yield_async(
            TaskStatus(state=TaskState.input_required, message=create_text_message_object(content="Need input"))
        )
        return f"async_function_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(async_function_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def async_generator_resume_agent(message: Message, context: RunContext):
        """Asynchronous generator agent that requires input and handles resume."""
        yield "async_generator_resume_agent: starting"
        resume_message = yield TaskStatus(
            state=TaskState.input_required, message=create_text_message_object(content="Need input")
        )
        yield f"async_generator_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(async_generator_resume_agent) as (server, client):
        yield server, client


async def test_sync_function_agent(sync_function_agent):
    """Test synchronous function agent that returns a string directly."""
    server, client = sync_function_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    assert "sync_function_agent: hello" in response.root.result.history[-1].parts[0].root.text


async def test_sync_function_with_context_agent(sync_function_with_context_agent):
    """Test synchronous function agent with context using context.yield_sync."""
    server, client = sync_function_with_context_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    # Should have intermediate yield and final result
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "first sync yield" in messages
    assert "sync_function_with_context_agent: hello" in messages


async def test_sync_generator_agent(sync_generator_agent):
    """Test synchronous generator agent using yield statements."""
    server, client = sync_generator_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "sync_generator yield 1" in messages
    assert "sync_generator yield 2" in messages


async def test_sync_generator_with_context_agent(sync_generator_with_context_agent):
    """Test synchronous generator agent with context using both yields and context.yield_sync."""
    server, client = sync_generator_with_context_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "sync_generator_with_context yield 1" in messages
    assert "sync_generator_with_context context yield" in messages
    assert "sync_generator_with_context yield 2" in messages
    assert "sync_generator_with_context_agent: hello" in messages


async def test_async_function_agent(async_function_agent):
    """Test asynchronous function agent that returns a string directly."""
    server, client = async_function_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    assert "async_function_agent: hello" in response.root.result.history[-1].parts[0].root.text


async def test_async_function_with_context_agent(async_function_with_context_agent):
    """Test asynchronous function agent with context using context.yield_async."""
    server, client = async_function_with_context_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "first async yield" in messages
    assert "async_function_with_context_agent: hello" in messages


async def test_async_generator_agent(async_generator_agent):
    """Test asynchronous generator agent using yield statements."""
    server, client = async_generator_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "async_generator yield 1" in messages
    assert "async_generator yield 2" in messages
    assert "async_generator_agent: hello" in messages


async def test_async_generator_with_context_agent(async_generator_with_context_agent):
    """Test asynchronous generator agent with context using both yields and context.yield_async."""
    server, client = async_generator_with_context_agent
    request = create_send_request_object("hello")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "async_generator_with_context yield 1" in messages
    assert "async_generator_with_context context yield" in messages
    assert "async_generator_with_context yield 2" in messages
    assert "async_generator_with_context_agent: hello" in messages


async def test_sync_function_resume_agent(sync_function_resume_agent):
    """Test synchronous function agent with resume functionality."""
    server, client = sync_function_resume_agent
    request = create_send_request_object("initial")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.input_required

    resume_request = create_send_request_object("resume data", response.root.result.id)
    resume_response = await client.send_message(request=resume_request)

    assert resume_response.root.result.status.state == TaskState.completed
    assert (
        "sync_function_resume_agent: received resume data" in resume_response.root.result.history[-1].parts[0].root.text
    )


async def test_sync_generator_resume_agent(sync_generator_resume_agent):
    """Test synchronous generator agent with resume functionality."""
    server, client = sync_generator_resume_agent
    request = create_send_request_object("initial")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.input_required
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "sync_generator_resume_agent: starting" in messages

    resume_request = create_send_request_object("resume data", response.root.result.id)
    resume_response = await client.send_message(request=resume_request)

    assert resume_response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in resume_response.root.result.history if msg.role.value == "agent"]
    assert "sync_generator_resume_agent: received resume data" in messages


async def test_async_function_resume_agent(async_function_resume_agent):
    """Test asynchronous function agent with resume functionality."""
    server, client = async_function_resume_agent
    request = create_send_request_object("initial")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.input_required

    resume_request = create_send_request_object("resume data", response.root.result.id)
    resume_response = await client.send_message(request=resume_request)

    assert resume_response.root.result.status.state == TaskState.completed
    assert (
        "async_function_resume_agent: received resume data"
        in resume_response.root.result.history[-1].parts[0].root.text
    )


async def test_async_generator_resume_agent(async_generator_resume_agent):
    """Test asynchronous generator agent with resume functionality."""
    server, client = async_generator_resume_agent
    request = create_send_request_object("initial")
    response = await client.send_message(request=request)

    assert response.root.result.status.state == TaskState.input_required
    messages = [msg.parts[0].root.text for msg in response.root.result.history if msg.role.value == "agent"]
    assert "async_generator_resume_agent: starting" in messages

    resume_request = create_send_request_object("resume data", response.root.result.id)
    resume_response = await client.send_message(request=resume_request)

    assert resume_response.root.result.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in resume_response.root.result.history if msg.role.value == "agent"]
    assert "async_generator_resume_agent: received resume data" in messages


async def test_sync_function_streaming(sync_function_agent):
    """Test synchronous function agent with streaming."""
    server, client = sync_function_agent
    events = []
    async for event in client.send_message_streaming(request=create_streaming_request_object("hello")):
        events.append(event)

    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    assert status_events[-1].root.result.status.state == TaskState.completed


async def test_sync_generator_streaming(sync_generator_agent):
    """Test synchronous generator agent with streaming to see intermediate yields."""
    server, client = sync_generator_agent
    events = []
    async for event in client.send_message_streaming(request=create_streaming_request_object("hello")):
        events.append(event)

    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    assert status_events[-1].root.result.status.state == TaskState.completed

    # Should see multiple working state messages for each yield
    working_events = [e for e in status_events if e.root.result.status.state == TaskState.working]
    assert len(working_events) >= 3  # At least 3 yields from the generator


async def test_async_generator_streaming(async_generator_agent):
    """Test asynchronous generator agent with streaming to see intermediate yields."""
    server, client = async_generator_agent
    events = []
    async for event in client.send_message_streaming(request=create_streaming_request_object("hello")):
        events.append(event)

    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    assert status_events[-1].root.result.status.state == TaskState.completed

    # Should see multiple working state messages for each yield
    working_events = [e for e in status_events if e.root.result.status.state == TaskState.working]
    assert len(working_events) >= 2  # At least 2 yields from the generator
