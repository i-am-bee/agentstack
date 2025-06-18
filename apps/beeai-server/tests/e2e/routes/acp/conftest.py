import asyncio
import base64
import time
from threading import Thread
from typing import AsyncIterator, AsyncGenerator, Iterator

import httpx
import pytest
from acp_sdk.server import Server, Context

from acp_sdk import (
    MessageAwaitRequest,
    AwaitResume,
    Error,
    ACPError,
    Artifact,
    ErrorCode,
    Message,
    MessagePart,
    ResourceUrl,
)

"""
These tests are copied from acp repository: 
https://github.com/i-am-bee/acp/blob/main/python/tests/e2e/test_suites/test_runs.py
"""

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def server(request: pytest.FixtureRequest, clean_up_fn, test_configuration) -> Iterator[None]:
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
    async def history_echo(input: list[Message], context: Context) -> AsyncIterator[Message]:
        # TODO: hack - session url is wrong when self-registered
        context.session.history = [
            ResourceUrl(str(url).replace("host.docker.internal", "localhost")) for url in context.session.history
        ]

        async for message in context.session.load_history():
            yield message
        for message in input:
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
        assert context.session is not None

        yield MessagePart(content=str(context.session.id), content_type="text/plain")

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

    @server.agent()
    async def file_reader(input: list[Message], context: Context) -> AsyncGenerator[Message, None]:
        for message in input:
            for part in message.parts:
                if part.content_url:
                    async with httpx.AsyncClient() as client:
                        content = await client.get(str(part.content_url))
                        content_type = content.headers.get("Content-Type") or part.content_type
                        yield MessagePart(content=content.content, content_type=content_type)

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
