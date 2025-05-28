import asyncio
import base64
import time
from threading import Thread
from typing import AsyncIterator, AsyncGenerator, Iterator

import httpx
import pytest
from acp_sdk.server import Server, Context

from acp_sdk.client import Client
from acp_sdk import (
    MessageAwaitRequest,
    AwaitResume,
    Error,
    ACPError,
    Artifact,
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


"""
These tests are copied from acp repository: 
https://github.com/i-am-bee/acp/blob/main/python/tests/e2e/test_suites/test_runs.py
"""

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def server(request: pytest.FixtureRequest, test_configuration, clean_up_fn) -> Iterator[None]:
    server = Server()

    @server.agent()
    async def echo(input: list[Message], context: Context) -> AsyncIterator[Message]:
        for message in input:
            yield message

    @server.agent()
    async def slow_echo(input: list[Message], context: Context) -> AsyncIterator[Message]:
        for message in input:
            await asyncio.sleep(1)
            yield message

    @server.agent()
    async def awaiter(
        input: list[Message], context: Context
    ) -> AsyncGenerator[Message | MessageAwaitRequest, AwaitResume]:
        yield MessageAwaitRequest(message=Message(parts=[]))
        yield MessagePart(content="empty", content_type="text/plain")

    @server.agent()
    async def failer(input: list[Message], context: Context) -> AsyncIterator[Message]:
        yield Error(code=ErrorCode.INVALID_INPUT, message="Wrong question buddy!")
        raise RuntimeError("Unreachable code")

    @server.agent()
    async def raiser(input: list[Message], context: Context) -> AsyncIterator[Message]:
        raise ACPError(Error(code=ErrorCode.INVALID_INPUT, message="Wrong question buddy!"))

    @server.agent()
    async def sessioner(input: list[Message], context: Context) -> AsyncIterator[Message]:
        assert context.session_id is not None

        yield MessagePart(content=str(context.session_id), content_type="text/plain")

    @server.agent()
    async def mime_types(input: list[Message], context: Context) -> AsyncIterator[Message]:
        yield MessagePart(content="<h1>HTML Content</h1>", content_type="text/html")
        yield MessagePart(content='{"key": "value"}', content_type="application/json")
        yield MessagePart(content="console.log('Hello');", content_type="application/javascript")
        yield MessagePart(content="body { color: red; }", content_type="text/css")

    @server.agent()
    async def base64_encoding(input: list[Message], context: Context) -> AsyncIterator[Message]:
        yield Message(
            parts=[
                MessagePart(
                    content=base64.b64encode(
                        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                    ).decode("ascii"),
                    content_type="image/png",
                    content_encoding="base64",
                ),
                MessagePart(content="This is plain text", content_type="text/plain"),
            ]
        )

    @server.agent()
    async def artifact_producer(input: list[Message], context: Context) -> AsyncGenerator[Message | Artifact, None]:
        yield MessagePart(content="Processing with artifacts", content_type="text/plain")
        yield Artifact(name="text-result.txt", content_type="text/plain", content="This is a text artifact result")
        yield Artifact(
            name="data.json", content_type="application/json", content='{"results": [1, 2, 3], "status": "complete"}'
        )
        yield Artifact(
            name="image.png",
            content_type="image/png",
            content=base64.b64encode(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            ).decode("ascii"),
            content_encoding="base64",
        )

    try:
        thread = Thread(target=server.run, kwargs={"port": 9999}, daemon=True)
        thread.start()
        with httpx.Client(base_url=f"{test_configuration.server_url}/api/v1") as client:
            for attempt in range(10):
                if client.get("providers").json()["items"]:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Server did not start or register itself correctly")

            yield server
    finally:
        asyncio.run(clean_up_fn())
        server.should_exit = True
        thread.join(timeout=2)


input = [Message(parts=[MessagePart(content="Hello!")])]
await_resume = MessageAwaitResume(message=Message(parts=[]))


@pytest.mark.asyncio
async def test_run_sync(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_sync(agent="echo", input=input)
    assert run.status == RunStatus.COMPLETED
    assert run.output == input


@pytest.mark.asyncio
async def test_run_async(server: Server, acp_client: Client) -> None:
    run = await acp_client.run_async(agent="echo", input=input)
    assert run.status == RunStatus.CREATED


@pytest.mark.asyncio
async def test_run_stream(server: Server, acp_client: Client) -> None:
    event_stream = [event async for event in acp_client.run_stream(agent="echo", input=input)]
    assert isinstance(event_stream[0], RunCreatedEvent)
    assert isinstance(event_stream[-1], RunCompletedEvent)
    assert event_stream[-1].run.output == input


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
@pytest.mark.skip(reason="TODO: Runs do not enter cancelled state")  # TODO
async def test_run_cancel(server: Server, acp_client: Client, agent: AgentName) -> None:
    run = await acp_client.run_async(agent=agent, input=input)
    run = await acp_client.run_cancel(run_id=run.run_id)
    assert run.status == RunStatus.CANCELLING
    await asyncio.sleep(2)
    run = await acp_client.run_status(run_id=run.run_id)
    assert run.status == RunStatus.CANCELLED


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", ["slow_echo"])
@pytest.mark.skip(reason="TODO: Runs do not enter cancelled state")  # TODO
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
async def test_run_session(server: Server, acp_client: Client) -> None:
    async with acp_client.session() as session:
        run = await session.run_sync(agent="echo", input=input)
        assert run.output == input
        run = await session.run_sync(agent="echo", input=input)
        assert run.output == input + input + input


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
