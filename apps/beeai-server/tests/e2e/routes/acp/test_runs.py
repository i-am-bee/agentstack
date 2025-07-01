# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import base64

import pytest
from acp_sdk.client import Client
from acp_sdk.models import (
    AgentName,
    ArtifactEvent,
    ErrorCode,
    Message,
    MessageAwaitResume,
    MessagePart,
    MessagePartEvent,
    RunCancelledEvent,
    RunCompletedEvent,
    RunCreatedEvent,
    RunInProgressEvent,
    RunStatus,
)
from acp_sdk.server import Server

"""
These tests are copied from acp repository: 
https://github.com/i-am-bee/acp/blob/main/python/tests/e2e/test_suites/test_runs.py
"""

pytestmark = pytest.mark.e2e

input = [Message(parts=[MessagePart(content="Hello!")])]
output = [message.model_copy(update={"role": "agent/echo"}) for message in input]
await_resume = MessageAwaitResume(message=Message(parts=[]))


@pytest.mark.asyncio
async def test_run_sync(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="echo", input=input)
    assert run.status == RunStatus.COMPLETED
    assert run.output == output


@pytest.mark.asyncio
async def test_run_async(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_async(agent="echo", input=input)
    assert run.status == RunStatus.CREATED


@pytest.mark.asyncio
async def test_run_stream(server: Server, acp_client: Client) -> None:
    event_stream = [event async for event in acp_client.run_stream(agent="echo", input=input)]
    assert isinstance(event_stream[0], RunCreatedEvent)
    assert isinstance(event_stream[-1], RunCompletedEvent)
    assert event_stream[-1].run.output == output


@pytest.mark.asyncio
async def test_run_status(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_async(agent="echo", input=input)
    while run.status in (RunStatus.CREATED, RunStatus.IN_PROGRESS):
        run = await acp_client.run_status(run_id=run.run_id)
    assert run.status == RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_run_events(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="echo", input=input)
    events = [event async for event in acp_client.run_events(run_id=run.run_id)]
    assert isinstance(events[0], RunCreatedEvent)
    assert isinstance(events[-1], RunCompletedEvent)


@pytest.mark.asyncio
async def test_run_events_are_stream(server: Server, acp_client: Client) -> None:
    stream = [event async for event in acp_client.run_stream(agent="echo", input=input)]
    print(stream)
    assert isinstance(stream[0], RunCreatedEvent)
    events = [event async for event in acp_client.run_events(run_id=stream[0].run.run_id)]
    print(events)
    assert stream == events


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", ["failer", "raiser"])
async def test_failure(server: Server, acp_client: Client, agent: AgentName) -> None:
    run = await acp_client.run_sync(agent=agent, input=input)
    assert run.status == RunStatus.FAILED
    assert run.error is not None
    assert run.error.code == ErrorCode.INVALID_INPUT


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", ["awaiter", "slow_echo"])
async def test_run_cancel(server: Server, acp_client: Client, agent: AgentName) -> None:
    run = await acp_client.run_async(agent=agent, input=input)
    run = await acp_client.run_cancel(run_id=run.run_id)
    assert run.status == RunStatus.CANCELLING
    await asyncio.sleep(2)
    run = await acp_client.run_status(run_id=run.run_id)
    assert run.status == RunStatus.CANCELLED


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", ["slow_echo"])
async def test_run_cancel_stream(server: Server, acp_client: Client, agent: AgentName) -> None:
    last_event = None
    async for event in acp_client.run_stream(agent=agent, input=input):
        last_event = event
        if isinstance(event, RunCreatedEvent):
            run = await acp_client.run_cancel(run_id=event.run.run_id)
            assert run.status == RunStatus.CANCELLING
    assert isinstance(last_event, RunCancelledEvent)


@pytest.mark.asyncio
async def test_run_resume_sync(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="awaiter", input=input)
    assert run.status == RunStatus.AWAITING
    assert run.await_request is not None

    run = await acp_client.run_resume_sync(run_id=run.run_id, await_resume=await_resume)
    assert run.status == RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_run_resume_async(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="awaiter", input=input)
    assert run.status == RunStatus.AWAITING
    assert run.await_request is not None

    run = await acp_client.run_resume_async(run_id=run.run_id, await_resume=await_resume)
    assert run.status == RunStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_run_resume_stream(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="awaiter", input=input)
    assert run.status == RunStatus.AWAITING
    assert run.await_request is not None

    event_stream = [event async for event in acp_client.run_resume_stream(run_id=run.run_id, await_resume=await_resume)]
    assert isinstance(event_stream[0], RunInProgressEvent)
    assert isinstance(event_stream[-1], RunCompletedEvent)


@pytest.mark.asyncio
async def test_mime_types(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="mime_types", input=input)
    assert run.status == RunStatus.COMPLETED
    assert len(run.output) == 1

    message_parts = run.output[0].parts
    content_types = [part.content_type for part in message_parts]

    assert "text/html" in content_types
    assert "application/json" in content_types
    assert "application/javascript" in content_types
    assert "text/css" in content_types

    for part in message_parts:
        if part.content_type == "text/html":
            assert part.content == "<h1>HTML Content</h1>"
        elif part.content_type == "application/json":
            assert part.content == '{"key": "value"}'


@pytest.mark.asyncio
async def test_base64_encoding(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="base64_encoding", input=input)
    assert run.status == RunStatus.COMPLETED
    assert len(run.output) == 1

    message_parts = run.output[0].parts
    assert len(message_parts) == 2

    base64_part = next((part for part in message_parts if part.content_encoding == "base64"), None)
    assert base64_part is not None
    assert base64_part.content_type == "image/png"
    assert base64_part.content is not None

    text_part = next((part for part in message_parts if part.content_type == "text/plain"), None)
    assert text_part is not None
    assert text_part.content == "This is plain text"
    assert text_part.content_encoding == "plain"


@pytest.mark.asyncio
async def test_artifacts(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="artifact_producer", input=input)
    assert run.status == RunStatus.COMPLETED

    assert len(run.output) == 1
    assert run.output[0].parts[0].content == "Processing with artifacts"

    assert len(run.output[0].parts) == 4

    text_artifact = next((a for a in run.output[0].parts if a.name == "text-result.txt"), None)
    json_artifact = next((a for a in run.output[0].parts if a.name == "data.json"), None)
    image_artifact = next((a for a in run.output[0].parts if a.name == "image.png"), None)

    assert text_artifact is not None
    assert text_artifact.content_type == "text/plain"
    assert text_artifact.content == "This is a text artifact result"
    assert text_artifact.content_encoding == "plain"

    assert json_artifact is not None
    assert json_artifact.content_type == "application/json"
    assert json_artifact.content == '{"results": [1, 2, 3], "status": "complete"}'

    assert image_artifact is not None
    assert image_artifact.content_type == "image/png"
    assert image_artifact.content_encoding == "base64"
    base64.b64decode(image_artifact.content)


@pytest.mark.asyncio
async def test_artifact_streaming(server: Server, acp_client: Client) -> None:
    events = [event async for event in acp_client.run_stream(agent="artifact_producer", input=input)]

    assert isinstance(events[0], RunCreatedEvent)
    assert isinstance(events[-1], RunCompletedEvent)

    message_part_events = [e for e in events if isinstance(e, MessagePartEvent)]
    artifact_events = [e for e in events if isinstance(e, ArtifactEvent)]

    assert len(message_part_events) == 1
    assert message_part_events[0].part.content == "Processing with artifacts"

    assert len(artifact_events) == 3

    artifact_types = [a.part.content_type for a in artifact_events]
    assert "text/plain" in artifact_types
    assert "application/json" in artifact_types
    assert "image/png" in artifact_types
