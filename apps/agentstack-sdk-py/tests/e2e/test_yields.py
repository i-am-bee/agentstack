# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator, AsyncIterator

import pytest
from a2a.client import Client, ClientEvent, create_text_message_object
from a2a.types import (
    Artifact,
    Message,
    Part,
    Role,
    SendMessageRequest,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Value

from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage, InputRequired, Metadata, RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

pytestmark = pytest.mark.e2e


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task | None:
    """Helper to extract the final task from a client.send_message stream."""
    final_task = None
    async for event in stream:
        match event:
            case (_, task):
                final_task = task
            case (StreamResponse(status_update=TaskStatusUpdateEvent(status=TaskStatus(state=state))), task):
                if state in {TaskState.TASK_STATE_AUTH_REQUIRED, TaskState.TASK_STATE_INPUT_REQUIRED}:
                    break
                final_task = task
    return final_task


def create_send_request_object(text: str | None = None, task_id: str | None = None):
    message = create_text_message_object(content=text or "test")
    if task_id:
        message.task_id = task_id
    return SendMessageRequest(
        message=message,
    )


@pytest.fixture
async def sync_function_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_function_agent(message: Message):
        """Synchronous function agent that returns a string directly."""

        return f"sync_function_agent: {message.parts[0].text}"

    async with create_server_with_agent(sync_function_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_function_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_function_with_context_agent(message: Message, context: RunContext):
        """Synchronous function agent with context that uses context.yield_sync."""
        context.yield_sync("first sync yield")

        return f"sync_function_with_context_agent: {message.parts[0].text}"

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

        yield f"sync_generator_with_context_agent: {message.parts[0].text}"

    async with create_server_with_agent(sync_generator_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_function_agent(message: Message):
        """Asynchronous function agent that returns a string directly."""
        await asyncio.sleep(0.01)

        return f"async_function_agent: {message.parts[0].text}"

    async with create_server_with_agent(async_function_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_with_context_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_function_with_context_agent(message: Message, context: RunContext):
        """Asynchronous function agent with context that uses context.yield_async."""
        await context.yield_async("first async yield")
        await asyncio.sleep(0.01)

        return f"async_function_with_context_agent: {message.parts[0].text}"

    async with create_server_with_agent(async_function_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_generator_agent(message: Message):
        """Asynchronous generator agent that uses yield statements."""
        yield "async_generator yield 1"
        await asyncio.sleep(0.01)
        yield "async_generator yield 2"

        yield f"async_generator_agent: {message.parts[0].text}"

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

        yield f"async_generator_with_context_agent: {message.parts[0].text}"

    async with create_server_with_agent(async_generator_with_context_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_function_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_function_resume_agent(message: Message, context: RunContext):
        """Synchronous function agent that requires input and handles resume."""
        resume_message = context.yield_sync(
            TaskStatus(
                state=TaskState.TASK_STATE_INPUT_REQUIRED,
                message=create_text_message_object(content="Need input"),
            )
        )

        return f"sync_function_resume_agent: received {resume_message.parts[0].text}"

    async with create_server_with_agent(sync_function_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def sync_generator_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    def sync_generator_resume_agent(message: Message, context: RunContext):
        """Synchronous generator agent that requires input and handles resume."""
        yield "sync_generator_resume_agent: starting"
        resume_message = yield InputRequired(text="Need input")
        yield f"sync_generator_resume_agent: received {resume_message.parts[0].text}"

    async with create_server_with_agent(sync_generator_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_function_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_function_resume_agent(message: Message, context: RunContext):
        """Asynchronous function agent that requires input and handles resume."""
        resume_message = await context.yield_async(
            TaskStatus(
                state=TaskState.TASK_STATE_INPUT_REQUIRED, message=create_text_message_object(content="Need input")
            )
        )

        return f"async_function_resume_agent: received {resume_message.parts[0].text}"

    async with create_server_with_agent(async_function_resume_agent) as (server, client):
        yield server, client


@pytest.fixture
async def async_generator_resume_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def async_generator_resume_agent(message: Message, context: RunContext):
        """Asynchronous generator agent that requires input and handles resume."""
        yield "async_generator_resume_agent: starting"
        resume_message = yield InputRequired(text="Need input")
        yield f"async_generator_resume_agent: received {resume_message.parts[0].text}"

    async with create_server_with_agent(async_generator_resume_agent) as (server, client):
        yield server, client


async def test_sync_function_agent(sync_function_agent):
    """Test synchronous function agent that returns a string directly."""
    _, client = sync_function_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # pyrefly: ignore [missing-attribute, unsupported-operation]
    assert "sync_function_agent: hello" in final_task.history[-1].parts[0].text


async def test_sync_function_with_context_agent(sync_function_with_context_agent):
    """Test synchronous function agent with context using context.yield_sync."""
    _, client = sync_function_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # Consecutive string yields are accumulated into a single message
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert len(agent_messages) == 1
    text = agent_messages[0].parts[0].text
    assert "first sync yield" in text
    assert "sync_function_with_context_agent: hello" in text


async def test_sync_generator_agent(sync_generator_agent):
    """Test synchronous generator agent using yield statements."""
    _, client = sync_generator_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # Consecutive string yields are accumulated into a single message
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert len(agent_messages) == 1
    text = agent_messages[0].parts[0].text
    assert "sync_generator yield 1" in text
    assert "sync_generator yield 2" in text


async def test_sync_generator_with_context_agent(sync_generator_with_context_agent):
    """Test synchronous generator agent with context using both yields and context.yield_sync."""
    _, client = sync_generator_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # Consecutive string yields are accumulated into a single message
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert len(agent_messages) == 1
    text = agent_messages[0].parts[0].text
    assert "sync_generator_with_context yield 1" in text
    assert "sync_generator_with_context context yield" in text
    assert "sync_generator_with_context yield 2" in text
    assert "sync_generator_with_context_agent: hello" in text


async def test_async_function_agent(async_function_agent):
    """Test asynchronous function agent that returns a string directly."""
    _, client = async_function_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # pyrefly: ignore [missing-attribute, unsupported-operation]
    assert "async_function_agent: hello" in final_task.history[-1].parts[0].text


async def test_async_function_with_context_agent(async_function_with_context_agent):
    """Test asynchronous function agent with context using context.yield_async."""
    _, client = async_function_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # Consecutive string yields are accumulated into a single message
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert len(agent_messages) == 1
    text = agent_messages[0].parts[0].text
    assert "first async yield" in text
    assert "async_function_with_context_agent: hello" in text


async def test_async_generator_agent(async_generator_agent):
    """Test asynchronous generator agent using yield statements."""
    _, client = async_generator_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # Consecutive string yields are accumulated into a single message
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert len(agent_messages) == 1
    text = agent_messages[0].parts[0].text
    assert "async_generator yield 1" in text
    assert "async_generator yield 2" in text
    assert "async_generator_agent: hello" in text


async def test_async_generator_with_context_agent(async_generator_with_context_agent):
    """Test asynchronous generator agent with context using both yields and context.yield_async."""
    _, client = async_generator_with_context_agent
    message = create_text_message_object(content="hello")

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # Consecutive string yields are accumulated into a single message
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert len(agent_messages) == 1
    text = agent_messages[0].parts[0].text
    assert "async_generator_with_context yield 1" in text
    assert "async_generator_with_context context yield" in text
    assert "async_generator_with_context yield 2" in text
    assert "async_generator_with_context_agent: hello" in text


async def test_sync_function_resume_agent(sync_function_resume_agent):
    """Test synchronous function agent with resume functionality."""
    _, client = sync_function_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.TASK_STATE_INPUT_REQUIRED

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # pyrefly: ignore [missing-attribute, unsupported-operation]
    assert "sync_function_resume_agent: received resume data" in final_task.history[-1].parts[0].text


async def test_sync_generator_resume_agent(sync_generator_resume_agent):
    """Test synchronous generator agent with resume functionality."""
    _, client = sync_generator_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    # The "starting" string is flushed as a message before the InputRequired status
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in initial_task.history if msg.role == Role.ROLE_AGENT]
    assert any("sync_generator_resume_agent: starting" in msg.parts[0].text for msg in agent_messages)

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id
    resume_message.context_id = initial_task.context_id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert any("sync_generator_resume_agent: received resume data" in msg.parts[0].text for msg in agent_messages)


async def test_async_function_resume_agent(async_function_resume_agent):
    """Test asynchronous function agent with resume functionality."""
    _, client = async_function_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.TASK_STATE_INPUT_REQUIRED

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id

    # First interaction - should require input
    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # pyrefly: ignore [missing-attribute, unsupported-operation]
    assert "async_function_resume_agent: received resume data" in final_task.history[-1].parts[0].text


async def test_async_generator_resume_agent(async_generator_resume_agent):
    """Test asynchronous generator agent with resume functionality."""
    _, client = async_generator_resume_agent
    message = create_text_message_object(content="initial")

    # First interaction - should require input
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    assert initial_task.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
    # The "starting" string is flushed as a message before the InputRequired status
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in initial_task.history if msg.role == Role.ROLE_AGENT]
    assert any("async_generator_resume_agent: starting" in msg.parts[0].text for msg in agent_messages)

    # Resume with additional data
    resume_message = create_text_message_object(content="resume data")
    resume_message.task_id = initial_task.id
    resume_message.context_id = initial_task.context_id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert final_task is not None
    assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
    # pyrefly: ignore [missing-attribute, not-iterable]
    agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
    assert any("async_generator_resume_agent: received resume data" in msg.parts[0].text for msg in agent_messages)


async def test_sync_function_streaming(sync_function_agent):
    """Test synchronous function agent with streaming."""
    _, client = sync_function_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hello")):
        events.append(event)

    status_events = []
    for event in events:
        match event:
            case (StreamResponse(status_update=TaskStatusUpdateEvent() as status_update), _):
                status_events.append(status_update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.TASK_STATE_COMPLETED


async def test_sync_generator_streaming(sync_generator_agent):
    """Test synchronous generator agent with streaming events."""
    _, client = sync_generator_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hello")):
        events.append(event)

    status_events = []
    for event in events:
        match event:
            case (StreamResponse(status_update=TaskStatusUpdateEvent() as status_update), _):
                status_events.append(status_update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.TASK_STATE_COMPLETED

    # Without the streaming extension activated by the client, partial updates are not sent.
    # The final completed message contains the accumulated result.
    completed = status_events[-1]
    assert completed.status.message.parts[0].text


async def test_async_generator_streaming(async_generator_agent):
    """Test asynchronous generator agent with streaming events."""
    _, client = async_generator_agent
    events = []
    async for event in client.send_message(create_text_message_object(content="hello")):
        events.append(event)

    status_events = []
    for resp, _ in events:
        if MessageToDict(resp.status_update.status):
            status_events.append(resp.status_update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.TASK_STATE_COMPLETED

    # Without the streaming extension activated by the client, partial updates are not sent.
    # The final completed message contains the accumulated result.
    completed = status_events[-1]
    assert completed.status.message.parts[0].text


async def test_yield_dict_vs_metadata(create_server_with_agent):
    async def yielder_of_meta_data() -> AsyncIterator[RunYield]:
        # dict → Part(data=...), Metadata, and AgentMessage are accumulated into one message
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
        assert final_task.status.state == TaskState.TASK_STATE_COMPLETED
        # dict+Metadata are accumulated, then flushed as draft when AgentMessage arrives
        # The final message merges the draft (data part + metadata) with the AgentMessage (metadata)
        # pyrefly: ignore [missing-attribute, not-iterable]
        agent_messages = [msg for msg in final_task.history if msg.role == Role.ROLE_AGENT]
        assert len(agent_messages) == 1
        merged = agent_messages[0]
        # pyrefly: ignore [missing-attribute, unsupported-operation]
        assert MessageToDict(merged.parts[0].data) == {"data": "this should be datapart"}
        # Metadata from both Metadata yield and AgentMessage are merged
        # pyrefly: ignore [unsupported-operation]
        merged_meta = MessageToDict(merged.metadata)
        assert merged_meta["metadata"] == "this class still behaves as dict"
        assert merged_meta["metadata2"] == "and can be used in union"


async def test_yield_of_all_types(create_server_with_agent):
    async def yielder_of_all_types_agent(message: Message, context: RunContext) -> AsyncIterator[RunYield]:
        """Agent that yields all supported types."""
        text_part = Part(text="text")
        message = AgentMessage(parts=[text_part], role=Role.ROLE_AGENT, message_id=str(uuid.uuid4()))
        yield message
        yield text_part
        yield TaskStatus(message=message, state=TaskState.TASK_STATE_WORKING)
        yield AgentArtifact(parts=[text_part])
        yield Part(raw=b"0", filename="test.txt")
        yield Part(data=ParseDict({"a": 1}, Value()))
        yield TaskStatusUpdateEvent(
            status=TaskStatus(state=TaskState.TASK_STATE_WORKING, message=message),
            task_id=context.task_id,
            context_id=context.context_id,
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
                case (
                    StreamResponse(
                        status_update=TaskStatusUpdateEvent(status=TaskStatus(message=Message(message_id=message_id)))
                    ),
                    _,
                ) if message_id:
                    message_cnt += 1
                case (
                    StreamResponse(artifact_update=TaskArtifactUpdateEvent(artifact=Artifact(artifact_id=artifact_id))),
                    _,
                ) if artifact_id:
                    artifact_cnt += 1
        # With streaming accumulation:
        # - Message yield → 1 message
        # - text_part accumulated, then TaskStatus flushes → 1 merged message
        # - Parts accumulated, then TaskStatusUpdateEvent flushes → 1 merged message
        # - str/dict/Metadata accumulated, then completion flushes → 1 message
        assert message_cnt == 4
        assert artifact_cnt == 2
