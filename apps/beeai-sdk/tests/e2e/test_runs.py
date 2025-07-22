# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid

from a2a.client import A2AClient, create_text_message_object
from a2a.types import (
    CancelTaskRequest,
    GetTaskRequest,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskQueryParams,
    TaskState,
    TaskStatusUpdateEvent,
)

from beeai_sdk.server import Server

input_text = "Hello"


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


async def test_run_sync(echo: tuple[Server, A2AClient]) -> None:
    server, client = echo
    request = create_send_request_object()
    response = await client.send_message(request=request)
    assert response.root.result.status.state == TaskState.completed
    [input_message, output_message] = response.root.result.history
    assert input_message.message_id == request.params.message.message_id
    assert output_message.parts[0].root.text == request.params.message.parts[0].root.text


async def test_run_stream(echo: tuple[Server, A2AClient]) -> None:
    server, client = echo
    events = []
    async for event in client.send_message_streaming(request=create_streaming_request_object()):
        events.append(event)

    # Should receive TaskStatusUpdateEvents
    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    # Final event should be completion
    assert status_events[-1].root.result.status.state == TaskState.completed


async def test_run_status(echo: tuple[Server, A2AClient]) -> None:
    server, client = echo
    response = await client.send_message(request=create_send_request_object())
    task_id = response.root.result.id

    # Get current task status - should be completed for echo agent
    task_request = GetTaskRequest(id=str(uuid.uuid4()), params=TaskQueryParams(id=task_id))
    task_response = await client.get_task(request=task_request)
    assert hasattr(task_response.root.result, "status")
    assert task_response.root.result.status.state == TaskState.completed


async def test_failure_failer(failer: tuple[Server, A2AClient]) -> None:
    server, client = failer
    response = await client.send_message(request=create_send_request_object())
    # Failer agent should fail
    assert response.root.result.status.state == TaskState.failed


async def test_failure_raiser(raiser: tuple[Server, A2AClient]) -> None:
    server, client = raiser
    response = await client.send_message(request=create_send_request_object())
    # Raiser agent should fail
    assert response.root.result.status.state == TaskState.failed


async def test_run_cancel_awaiter(awaiter: tuple[Server, A2AClient]) -> None:
    server, client = awaiter
    # Start a task
    response = await client.send_message(request=create_send_request_object())
    task_id = response.root.result.id

    cancel_request = CancelTaskRequest(id=str(uuid.uuid4()), params=TaskIdParams(id=task_id))
    await client.cancel_task(request=cancel_request)
    # Check final status
    task_request = GetTaskRequest(id=str(uuid.uuid4()), params=TaskQueryParams(id=task_id))
    task_response = await client.get_task(request=task_request)
    assert task_response.root.result.status.state == TaskState.canceled


async def test_run_cancel_slow_echo(slow_echo: tuple[Server, A2AClient]) -> None:
    server, client = slow_echo
    # Start a task
    response = await client.send_message(request=create_send_request_object())
    task_id = response.root.result.id

    cancel_request = CancelTaskRequest(id=str(uuid.uuid4()), params=TaskIdParams(id=task_id))
    await client.cancel_task(request=cancel_request)
    # Check final status
    task_request = GetTaskRequest(id=str(uuid.uuid4()), params=TaskQueryParams(id=task_id))
    task_response = await client.get_task(request=task_request)
    assert hasattr(task_response.root.result, "status")
    assert task_response.root.result.status.state == TaskState.canceled


async def test_run_cancel_stream(slow_echo: tuple[Server, A2AClient]) -> None:
    server, client = slow_echo
    task_id = None
    cancelled = False
    states = []

    async for event in client.send_message_streaming(request=create_streaming_request_object()):
        if isinstance(event.root.result, TaskStatusUpdateEvent):
            if not cancelled and event.root.result.status.state == TaskState.working:
                task_id = event.root.result.task_id
                cancel_request = CancelTaskRequest(id=str(uuid.uuid4()), params=TaskIdParams(id=task_id))
                await client.cancel_task(request=cancel_request)
                cancelled = True

            states.append(event.root.result.status.state)

    assert states == [TaskState.working, TaskState.canceled]


async def test_run_resume_sync(awaiter: tuple[Server, A2AClient]) -> None:
    server, client = awaiter
    response = await client.send_message(request=create_send_request_object())

    assert response.root.result.status.state == TaskState.input_required
    resume_message = create_send_request_object("Resume input", response.root.result.id)
    resumed_response = await client.send_message(request=resume_message)
    assert hasattr(resumed_response.root.result, "status")
    assert resumed_response.root.result.status.state == TaskState.completed
    assert "Received resume: Resume input" in resumed_response.root.result.history[-1].parts[0].root.text


async def test_run_resume_stream(awaiter: tuple[Server, A2AClient]) -> None:
    server, client = awaiter
    response = await client.send_message(request=create_send_request_object())

    resume_message = create_streaming_request_object("Resume input", response.root.result.id)

    events = []
    async for event in client.send_message_streaming(request=resume_message):
        events.append(event)

    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    assert status_events[-1].root.result.status.state == TaskState.completed


async def test_artifacts(artifact_producer: tuple[Server, A2AClient]) -> None:
    server, client = artifact_producer
    response = await client.send_message(request=create_send_request_object())
    assert hasattr(response.root.result, "status")
    assert response.root.result.status.state == TaskState.completed

    # Check for artifacts in the task
    assert response.root.result.artifacts is not None
    artifacts = response.root.result.artifacts
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


async def test_artifact_streaming(artifact_producer: tuple[Server, A2AClient]) -> None:
    server, client = artifact_producer
    events = []
    async for event in client.send_message_streaming(request=create_streaming_request_object()):
        events.append(event)

    # Check for status events
    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    assert status_events[-1].root.result.status.state == TaskState.completed

    # Check for artifact events
    artifact_events = [e for e in events if isinstance(e.root.result, TaskArtifactUpdateEvent)]
    assert len(artifact_events) >= 3  # Should have text, json, and image artifacts

    # Verify artifact event properties
    artifact_names = [e.root.result.artifact.name for e in artifact_events]
    assert "text-result.txt" in artifact_names
    assert "data.json" in artifact_names
    assert "image.png" in artifact_names

    # Check specific artifact content in streaming
    text_event = next((e for e in artifact_events if e.root.result.artifact.name == "text-result.txt"), None)
    assert text_event is not None
    # Check artifact parts structure
    assert len(text_event.root.result.artifact.parts) > 0
    text_part = text_event.root.result.artifact.parts[0].root
    assert hasattr(text_part, "text")
    assert text_part.text == "This is a text artifact result"
    assert text_event.root.result.last_chunk is True  # Should be complete artifacts


async def test_chunked_artifacts(chunked_artifact_producer: tuple[Server, A2AClient]) -> None:
    server, client = chunked_artifact_producer
    # Test chunked artifacts by streaming from chunked_artifact_producer agent
    events = []
    async for event in client.send_message_streaming(request=create_streaming_request_object()):
        events.append(event)

    # Check for status events
    status_events = [e for e in events if isinstance(e.root.result, TaskStatusUpdateEvent)]
    assert len(status_events) > 0
    assert status_events[-1].root.result.status.state == TaskState.completed

    # Check for artifact events - should have 3 chunks for the same artifact
    artifact_events = [e for e in events if isinstance(e.root.result, TaskArtifactUpdateEvent)]
    chunked_events = [e for e in artifact_events if e.root.result.artifact.name == "large-file.txt"]
    assert len(chunked_events) == 3  # Should have 3 chunks

    # Verify chunk properties
    first_chunk = chunked_events[0]
    second_chunk = chunked_events[1]
    final_chunk = chunked_events[2]

    # First chunk should not be last
    assert first_chunk.root.result.last_chunk is False
    assert first_chunk.root.result.append is False  # First chunk is not append

    # Second chunk should not be last and should be append
    assert second_chunk.root.result.last_chunk is False
    assert second_chunk.root.result.append is True  # Subsequent chunks are append

    # Final chunk should be last and append
    assert final_chunk.root.result.last_chunk is True
    assert final_chunk.root.result.append is True

    # Verify artifact content
    assert "first chunk" in first_chunk.root.result.artifact.parts[0].root.text
    assert "second chunk" in second_chunk.root.result.artifact.parts[0].root.text
    assert "final chunk" in final_chunk.root.result.artifact.parts[0].root.text
