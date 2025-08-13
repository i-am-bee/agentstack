# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Annotated

import pytest
from a2a.client import A2AClient
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, MessageSendParams, SendMessageRequest, TaskState
from beeai_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionClient,
    PlatformApiExtensionParams,
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.platform import File
from beeai_sdk.platform.context import Context, ContextPermissions
from beeai_sdk.server import Server


@pytest.fixture
async def file_reader_writer(create_server_with_agent) -> AsyncGenerator[tuple[Server, A2AClient]]:
    async def file_reader_writer(
        message: Message,
        ext: Annotated[
            PlatformApiExtensionServer, PlatformApiExtensionSpec(PlatformApiExtensionParams(auto_use=False))
        ],
    ) -> AsyncIterator[RunYield]:
        async with ext.use_client():
            yield await File.content(message.parts[0].root.text)
            file = await File.create(filename="1.txt", content=message.context_id.encode(), content_type="text/plain")
            yield file.id

    async with create_server_with_agent(file_reader_writer) as (server, test_client):
        yield server, test_client


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "permissions, should_fail",
    [
        (ContextPermissions(files={"read", "write"}), False),
        (ContextPermissions(files={"read"}), True),
    ],
)
@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_platform_api_extension(subtests, file_reader_writer, permissions, should_fail):
    server, client = file_reader_writer

    # create context and token
    context = await Context.create()
    token = await context.generate_token(grant_context_permissions=permissions)

    # upload test file
    file = await File.create(
        filename="test_file", content=b"Hello world", content_type="text/plain", context_id=context.id
    )

    # create message with auth credentials
    message = create_text_message_object(content=file.id)
    message.context_id = context.id
    api_extension_client = PlatformApiExtensionClient(PlatformApiExtensionSpec())
    message.metadata = api_extension_client.api_auth_metadata(auth_token=token.token, expires_at=token.expires_at)

    # send message
    resp = await client.send_message(SendMessageRequest(id=1, params=MessageSendParams(message=message)))

    if should_fail:
        assert resp.root.result.status.state == TaskState.failed
        assert "403 Forbidden" in resp.root.result.status.message.parts[0].root.text
    else:
        assert resp.root.result.status.state == TaskState.completed, (
            f"Fail: {resp.root.result.status.message.parts[0].root.text}"
        )

        # check that first message is the content of the first_file
        first_message_text = resp.root.result.history[1].parts[0].root.text
        assert first_message_text == "Hello world"

        # check that the agent uploaded a new file with correct context_id as content
        file_id = resp.root.result.history[2].parts[0].root.text
        assert await File.content(file_id) == context.id
