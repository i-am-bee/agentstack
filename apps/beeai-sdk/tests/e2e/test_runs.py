# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid
from collections.abc import AsyncIterator

import pytest
from a2a.client import Client, ClientEvent, create_text_message_object
from a2a.types import (
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskQueryParams,
    TaskState,
    TaskStatusUpdateEvent,
)

from beeai_sdk.server import Server

pytestmark = pytest.mark.e2e

input_text = "Hello"


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task:
    """Helper to extract the final task from a client.send_message stream."""
    final_task = None
    async for event in stream:
        match event:
            case (task, _):
                final_task = task
    return final_task


def create_send_request_object(text: str | None = None, task_id: str | None = None):
    message = create_text_message_object(content=text or input_text)
    if task_id:
        message.task_id = task_id
    return SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )


def create_streaming_request_object(text: str | None = None, task_id: str | None = None):
    message = create_text_message_object(content=text or input_text)
    if task_id:
        message.task_id = task_id
    return SendStreamingMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )


async def test_run_sync(echo: tuple[Server, Client]) -> None:
    _, client = echo
    message = create_text_message_object(content=input_text)

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    assert final_task.status.state == TaskState.completed
    assert len(final_task.history) >= 1
    # The echo agent should return the same text as input
    agent_messages = [msg for msg in final_task.history if msg.role.value == "agent"]
    assert len(agent_messages) >= 1
    assert agent_messages[0].parts[0].root.text == message.parts[0].root.text


async def test_run_stream(echo: tuple[Server, Client]) -> None:
    _, client = echo
    events = []
    async for event in client.send_message(create_text_message_object()):
        events.append(event)

    # Should receive TaskStatusUpdateEvents
    status_events = []
    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)

    assert len(status_events) > 0
    # Final event should be completion
    assert status_events[-1].status.state == TaskState.completed


async def test_run_status(echo: tuple[Server, Client]) -> None:
    _, client = echo
    message = create_text_message_object()

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    task_id = final_task.id

    # Get current task status - should be completed for echo agent
    task_params = TaskQueryParams(id=task_id)
    task_response = await client.get_task(task_params)
    assert hasattr(task_response, "status")
    assert task_response.status.state == TaskState.completed


async def test_failure_failer(failer: tuple[Server, Client]) -> None:
    _, client = failer
    message = create_text_message_object()

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    # Failer agent should fail
    assert final_task.status.state == TaskState.failed


async def test_failure_raiser(raiser: tuple[Server, Client]) -> None:
    _, client = raiser
    message = create_text_message_object()

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert final_task is not None
    # Raiser agent should fail
    assert final_task.status.state == TaskState.failed


async def test_run_cancel_awaiter(awaiter: tuple[Server, Client]) -> None:
    _, client = awaiter
    message = create_text_message_object()

    # Start a task
    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task is not None
    task_id = initial_task.id

    # Cancel the task
    cancel_params = TaskIdParams(id=task_id)
    await client.cancel_task(cancel_params)

    # Check final status
    task_params = TaskQueryParams(id=task_id)
    task_response = await client.get_task(task_params)
    assert task_response.status.state == TaskState.canceled


async def test_run_cancel_stream(slow_echo: tuple[Server, Client]) -> None:
    _, client = slow_echo
    task_id = None
    cancelled = False
    states = []

    async for event in client.send_message(create_text_message_object()):
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                if not cancelled and update.status.state == TaskState.working:
                    task_id = update.task_id
                    cancel_params = TaskIdParams(id=task_id)
                    await client.cancel_task(cancel_params)
                    cancelled = True
                states.append(update.status.state)

    assert states == [TaskState.working, TaskState.canceled]


async def test_run_resume_sync(awaiter: tuple[Server, Client]) -> None:
    _, client = awaiter
    message = create_text_message_object()

    initial_task = await get_final_task_from_stream(client.send_message(message))

    assert initial_task.status.state == TaskState.input_required

    resume_message = create_text_message_object(content="Resume input")
    resume_message.task_id = initial_task.id

    final_task = await get_final_task_from_stream(client.send_message(resume_message))

    assert hasattr(final_task, "status")
    assert final_task.status.state == TaskState.completed
    assert "Received resume: Resume input" in final_task.history[-1].parts[0].root.text


async def test_run_resume_stream(awaiter: tuple[Server, Client]) -> None:
    _, client = awaiter
    message = create_text_message_object()

    initial_task = await get_final_task_from_stream(client.send_message(message))

    resume_message = create_text_message_object(content="Resume input")
    resume_message.task_id = initial_task.id

    events = []
    async for event in client.send_message(resume_message):
        events.append(event)

    status_events = []
    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.completed


async def test_artifacts(artifact_producer: tuple[Server, Client]) -> None:
    _, client = artifact_producer
    message = create_text_message_object()

    final_task = await get_final_task_from_stream(client.send_message(message))

    assert hasattr(final_task, "status")
    assert final_task.status.state == TaskState.completed

    # Check for artifacts in the task
    assert final_task.artifacts is not None
    artifacts = final_task.artifacts
    assert len(artifacts) >= 3  # Should have text, json, and image artifacts

    # Check for specific artifacts by name
    artifact_names = [artifact.name for artifact in artifacts]
    assert "text-result.txt" in artifact_names
    assert "data.json" in artifact_names
    assert "image.png" in artifact_names

    # Verify artifact content types and data
    text_artifact = next((a for a in artifacts if a.name == "text-result.txt"), None)
    json_artifact = next((a for a in artifacts if a.name == "data.json"), None)
    image_artifact = next((a for a in artifacts if a.name == "image.png"), None)

    assert text_artifact is not None
    assert len(text_artifact.parts) > 0
    text_part = text_artifact.parts[0].root
    assert hasattr(text_part, "text")
    assert text_part.text == "This is a text artifact result"

    assert json_artifact is not None
    assert len(json_artifact.parts) > 0
    json_part = json_artifact.parts[0].root
    assert hasattr(json_part, "data")
    assert json_part.data == {"results": [1, 2, 3], "status": "complete"}

    assert image_artifact is not None
    assert len(image_artifact.parts) > 0
    image_part = image_artifact.parts[0].root
    assert hasattr(image_part, "file")
    # Verify it's valid PNG data by checking that it contains PNG in base64
    assert "iVBOR" in image_part.file.bytes  # PNG header in base64


async def test_artifact_streaming(artifact_producer: tuple[Server, Client]) -> None:
    _, client = artifact_producer
    events = []
    async for event in client.send_message(create_text_message_object()):
        events.append(event)

    # Check for status and artifact events using match-case
    status_events = []
    artifact_events = []

    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)
            case (_, TaskArtifactUpdateEvent() as update):
                artifact_events.append(update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.completed

    # Check for artifact events
    assert len(artifact_events) >= 3  # Should have text, json, and image artifacts

    # Verify artifact event properties
    artifact_names = [e.artifact.name for e in artifact_events]
    assert "text-result.txt" in artifact_names
    assert "data.json" in artifact_names
    assert "image.png" in artifact_names

    # Check specific artifact content in streaming
    text_event = next((e for e in artifact_events if e.artifact.name == "text-result.txt"), None)
    assert text_event is not None
    # Check artifact parts structure
    assert len(text_event.artifact.parts) > 0
    text_part = text_event.artifact.parts[0].root
    assert hasattr(text_part, "text")
    assert text_part.text == "This is a text artifact result"
    assert text_event.last_chunk is True  # Should be complete artifacts


async def test_chunked_artifacts(chunked_artifact_producer: tuple[Server, Client]) -> None:
    _, client = chunked_artifact_producer
    # Test chunked artifacts by streaming from chunked_artifact_producer agent
    events = []
    async for event in client.send_message(create_text_message_object()):
        events.append(event)

    # Check for status and artifact events using match-case
    status_events = []
    artifact_events = []

    for event in events:
        match event:
            case (_, TaskStatusUpdateEvent() as update):
                status_events.append(update)
            case (_, TaskArtifactUpdateEvent() as update):
                artifact_events.append(update)

    assert len(status_events) > 0
    assert status_events[-1].status.state == TaskState.completed

    # Check for artifact events - should have 3 chunks for the same artifact
    chunked_events = [e for e in artifact_events if e.artifact.name == "large-file.txt"]
    assert len(chunked_events) == 3  # Should have 3 chunks

    # Verify chunk properties
    first_chunk = chunked_events[0]
    second_chunk = chunked_events[1]
    final_chunk = chunked_events[2]

    # First chunk should not be last
    assert first_chunk.last_chunk is False
    assert first_chunk.append is False  # First chunk is not append

    # Second chunk should not be last and should be append
    assert second_chunk.last_chunk is False
    assert second_chunk.append is True  # Subsequent chunks are append

    # Final chunk should be last and append
    assert final_chunk.last_chunk is True
    assert final_chunk.append is True

    # Verify artifact content
    assert "first chunk" in first_chunk.artifact.parts[0].root.text
    assert "second chunk" in second_chunk.artifact.parts[0].root.text
    assert "final chunk" in final_chunk.artifact.parts[0].root.text
