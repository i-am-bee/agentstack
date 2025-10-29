# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid
from collections.abc import AsyncGenerator, AsyncIterator

import pytest
from a2a.client import Client, ClientEvent, create_text_message_object
from a2a.types import (
    DataPart,
    FilePart,
    FileWithBytes,
    Message,
    MessageSendParams,
    Role,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage, InputRequired, Metadata, RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

pytestmark = pytest.mark.e2e


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task:
    """Helper to extract the final task from a client.send_message stream."""
    final_task = None
    async for event in stream:
        match event:
            case (task, None):
                final_task = task
            case (task, TaskStatusUpdateEvent(status=TaskStatus(state=state))):
                if state in {TaskState.auth_required, TaskState.input_required}:
                    break
                final_task = task
    return final_task


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
async def sync_function_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_function_agent(message: Message):
        """Synchronous function agent that returns a string directly."""
        return f"sync_function_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(sync_function_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_function_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_function_with_context_agent(message: Message, context: RunContext):
        """Synchronous function agent with context that uses context.yield_sync."""
        context.yield_sync("first sync yield")
        return f"sync_function_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(sync_function_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_generator_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_generator_agent(message: Message):
        """Synchronous generator agent that uses yield statements."""
        yield "sync_generator yield 1"
        yield "sync_generator yield 2"

    async with create_server_with_agent(sync_generator_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_generator_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_generator_with_context_agent(message: Message, context: RunContext):
        """Synchronous generator agent with context using both yields and context.yield_sync."""
        yield "sync_generator_with_context yield 1"
        context.yield_sync("sync_generator_with_context context yield")
        yield "sync_generator_with_context yield 2"
        yield f"sync_generator_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(sync_generator_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_function_agent(message: Message):
        """Asynchronous function agent that returns a string directly."""
        await asyncio.sleep(0.01)
        return f"async_function_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_function_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_function_with_context_agent(message: Message, context: RunContext):
        """Asynchronous function agent with context that uses context.yield_async."""
        await context.yield_async("first async yield")
        await asyncio.sleep(0.01)
        return f"async_function_with_context_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_function_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_generator_agent(message: Message):
        """Asynchronous generator agent that uses yield statements."""
        yield "async_generator yield 1"
        await asyncio.sleep(0.01)
        yield "async_generator yield 2"
        yield f"async_generator_agent: {message.parts[0].root.text}"

    async with create_server_with_agent(async_generator_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
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
async def sync_function_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
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
async def sync_generator_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_generator_resume_agent(message: Message, context: RunContext):
        """Synchronous generator agent that requires input and handles resume."""
        yield "sync_generator_resume_agent: starting"
        resume_message = yield InputRequired(text="Need input")
        yield f"sync_generator_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(sync_generator_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_function_resume_agent(message: Message, context: RunContext):
        """Asynchronous function agent that requires input and handles resume."""
        resume_message = await context.yield_async(
            TaskStatus(state=TaskState.input_required, message=create_text_message_object(content="Need input"))
        )
        return f"async_function_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(async_function_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_generator_resume_agent(message: Message, context: RunContext):
        """Asynchronous generator agent that requires input and handles resume."""
        yield "async_generator_resume_agent: starting"
        resume_message = yield InputRequired(text="Need input")
        yield f"async_generator_resume_agent: received {resume_message.parts[0].root.text}"

    async with create_server_with_agent(async_generator_resume_agent) as (server, client):
        yield server, client


async def test_sync_function_agent(sync_function_agent):
    """Test synchronous function agent that returns a string directly."""
    _, client = sync_function_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    assert "sync_function_agent: hello" in final_task.history[-1].parts[0].root.text


async def test_sync_function_with_context_agent(sync_function_with_context_agent):
    """Test synchronous function agent with context using context.yield_sync."""
    _, client = sync_function_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    # Should have intermediate yield and final result
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "first sync yield" in messages
    assert "sync_function_with_context_agent: hello" in messages


async def test_sync_generator_agent(sync_generator_agent):
    """Test synchronous generator agent using yield statements."""
    _, client = sync_generator_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "sync_generator yield 1" in messages
    assert "sync_generator yield 2" in messages


async def test_sync_generator_with_context_agent(sync_generator_with_context_agent):
    """Test synchronous generator agent with context using both yields and context.yield_sync."""
    _, client = sync_generator_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "sync_generator_with_context yield 1" in messages
    assert "sync_generator_with_context context yield" in messages
    assert "sync_generator_with_context yield 2" in messages
    assert "sync_generator_with_context_agent: hello" in messages


async def test_async_function_agent(async_function_agent):
    """Test asynchronous function agent that returns a string directly."""
    _, client = async_function_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    assert "async_function_agent: hello" in final_task.history[-1].parts[0].root.text


async def test_async_function_with_context_agent(async_function_with_context_agent):
    """Test asynchronous function agent with context using context.yield_async."""
    _, client = async_function_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "first async yield" in messages
    assert "async_function_with_context_agent: hello" in messages


async def test_async_generator_agent(async_generator_agent):
    """Test asynchronous generator agent using yield statements."""
    _, client = async_generator_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "async_generator yield 1" in messages
    assert "async_generator yield 2" in messages
    assert "async_generator_agent: hello" in messages


async def test_async_generator_with_context_agent(async_generator_with_context_agent):
    """Test asynchronous generator agent with context using both yields and context.yield_async."""
    _, client = async_generator_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "async_generator_with_context yield 1" in messages
    assert "async_generator_with_context context yield" in messages
    assert "async_generator_with_context yield 2" in messages
    assert "async_generator_with_context_agent: hello" in messages


async def test_sync_function_resume_agent(sync_function_resume_agent):
    """Test synchronous function agent with resume functionality."""
    _, client = sync_function_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.input_required

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    assert "sync_function_resume_agent: received resume data" in final_task.history[-1].parts[0].root.text


async def test_sync_generator_resume_agent(sync_generator_resume_agent):
    """Test synchronous generator agent with resume functionality."""
    _, client = sync_generator_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.input_required
    messages = [msg.parts[0].root.text for msg in initial_task.history if msg.role.value == "agent"]
    assert "sync_generator_resume_agent: starting" in messages

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id
    resume_message.context_id = initial_task.context_id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "sync_generator_resume_agent: received resume data" in messages


async def test_async_function_resume_agent(async_function_resume_agent):
    """Test asynchronous function agent with resume functionality."""
    _, client = async_function_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.input_required

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id

    # First interaction - should require input
    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    assert "async_function_resume_agent: received resume data" in final_task.history[-1].parts[0].root.text


async def test_async_generator_resume_agent(async_generator_resume_agent):
    """Test asynchronous generator agent with resume functionality."""
    _, client = async_generator_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.input_required
    messages = [msg.parts[0].root.text for msg in initial_task.history if msg.role.value == "agent"]
    assert "async_generator_resume_agent: starting" in messages

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id
    resume_message.context_id = initial_task.context_id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    messages = [msg.parts[0].root.text for msg in final_task.history if msg.role.value == "agent"]
    assert "async_generator_resume_agent: received resume data" in messages


async def test_sync_function_streaming(sync_function_agent):
    """Test synchronous function agent with streaming."""
    _, client = sync_function_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hello")):
        events.append(event)

    status_events = []
    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.completed


async def test_sync_generator_streaming(sync_generator_agent):
    """Test synchronous generator agent with streaming to see intermediate yields."""
    _, client = sync_generator_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hello")):
        events.append(event)

    status_events = []
    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.completed

    # Should see multiple working state messages for each yield
    working_events = [e for e in status_events if e.status.state == TaskState.working]
    assert len(working_events) >= 3  # At least 3 yields from the generator


async def test_async_generator_streaming(async_generator_agent):
    """Test asynchronous generator agent with streaming to see intermediate yields."""
    _, client = async_generator_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hello")):
        events.append(event)

    status_events = []
    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.completed

    # Should see multiple working state messages for each yield
    working_events = [e for e in status_events if e.status.state == TaskState.working]
    assert len(working_events) >= 2  # At least 2 yields from the generator


async def test_yield_dict_vs_metadata(create_server_with_agent):
    async def yielder_of_meta_data() -> AsyncIterator[RunYield]:
        yield {"data": "this should be datapart"}
        yield Metadata({"metadata": "this should be metadata"})
        yield AgentMessage(
            metadata=Metadata({"metadata": "this class still behaves as dict"})
            | {"metadata2": "and can be used in union"}
        )

    async with create_server_with_agent(yielder_of_meta_data) as (_, client):
        message = create_text_message_object(content="hello")

        final_task = await get_final_task_from_stream(client.send_message(message))

        assert final_task is not None
        assert final_task.status.state == TaskState.completed
        assert final_task.history[0].parts[0].root.data == {"data": "this should be datapart"}
        assert final_task.history[1].metadata == {"metadata": "this should be metadata"}
        assert final_task.history[2].metadata == {
            "metadata": "this class still behaves as dict",
            "metadata2": "and can be used in union",
        }
        assert not final_task.history[0].metadata
        assert not final_task.history[1].parts
        assert not final_task.history[2].parts


async def test_yield_of_all_types(create_server_with_agent):
    async def yielder_of_all_types_agent(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        """Synchronous function agent that returns a string directly."""
        text_part = TextPart(text="text")
        message = AgentMessage(parts=[text_part], role=Role.agent, message_id=str(uuid.uuid4()))
        yield message
        yield text_part
        yield TaskStatus(message=message, state=TaskState.working)
        yield AgentArtifact(parts=[text_part])
        yield FilePart(file=FileWithBytes(bytes="0", name="test.txt"))
        yield DataPart(data={"a": 1})
        yield TaskStatusUpdateEvent(
            status=TaskStatus(state=TaskState.working, message=message),
            task_id=context.task_id,
            context_id=context.context_id,
            final=False,
        )
        yield TaskArtifactUpdateEvent(
            artifact=AgentArtifact(artifact_id=str(uuid.uuid4()), parts=[text_part]),
            context_id=context.context_id,
            task_id=context.task_id,
        )
        yield "text"
        yield {"data": "this is important"}
        yield Metadata({"metadata": "this, not so much"})

    async with create_server_with_agent(yielder_of_all_types_agent) as (_, client):
        message_cnt, artifact_cnt = 0, 0
        async for event in client.send_message(create_text_message_object(content="hello")):
            match event:
                case (Task(), TaskStatusUpdateEvent(status=TaskStatus(message=msg))) if msg:
                    message_cnt += 1
                case (Task(), TaskArtifactUpdateEvent()):
                    artifact_cnt += 1
        assert message_cnt == 9
        assert artifact_cnt == 2
