# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import os
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Annotated
from uuid import uuid4

import pytest
from a2a.client import Client, create_text_message_object
from a2a.types import FilePart, Message, Role, TaskState
from agentstack_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionClient,
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.platform import File, Provider
from agentstack_sdk.platform.context import Context, ContextPermissions
from agentstack_sdk.server import Server
from agentstack_sdk.util.file import load_file
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed

pytestmark = pytest.mark.e2e


@pytest.fixture
async def file_reader_writer(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def file_reader_writer(
        message: Message,
        _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
    ) -> AsyncIterator[RunYield]:
        for part in message.parts:
            match part.root:
                case FilePart() as fp:
                    async with load_file(fp, stream=True) as open_file:
                        async for chunk in open_file.aiter_text(chunk_size=5):
                            yield chunk

        file = await File.create(filename="1.txt", content=message.context_id.encode(), content_type="text/plain")
        yield file.to_file_part()

    async with create_server_with_agent(file_reader_writer) as (server, test_client):
        yield server, test_client


@pytest.mark.parametrize(
    "permissions, should_fail",
    [
        (ContextPermissions(files={"read", "write"}), False),
        (ContextPermissions(files={"read"}), True),
    ],
)
@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_platform_api_extension(file_reader_writer, permissions, should_fail, get_final_task_from_stream):
    _, client = file_reader_writer

    # create context and token
    context = await Context.create()
    token = await context.generate_token(grant_context_permissions=permissions)

    # upload test file
    file = await File.create(filename="f.txt", content=b"0123456789", content_type="text/plain", context_id=context.id)

    # create message with auth credentials
    api_extension_client = PlatformApiExtensionClient(PlatformApiExtensionSpec())

    message = Message(
        role=Role.user,
        parts=[file.to_file_part()],
        message_id=str(uuid4()),
        context_id=context.id,
        metadata=api_extension_client.api_auth_metadata(auth_token=token.token, expires_at=token.expires_at),
    )

    # send message
    task = await get_final_task_from_stream(client.send_message(message))

    if should_fail:
        assert task.status.state == TaskState.failed
        assert "403 Forbidden" in task.status.message.parts[0].root.text
    else:
        assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

        # check that first message is the content of the first_file
        first_message_text = task.history[0].parts[0].root.text
        assert first_message_text == "01234"

        second_message_text = task.history[1].parts[0].root.text
        assert second_message_text == "56789"

        # check that the agent uploaded a new file with correct context_id as content
        async with load_file(task.history[2].parts[0].root) as file:
            assert file.text == context.id


SELF_REGISTRATION_TEST_VAR_NAME = "_SELF_REGISTRATION_TEST_VAR"


@pytest.fixture
async def self_registration_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def self_registration_agent() -> AsyncIterator[RunYield]:
        yield os.environ.get(SELF_REGISTRATION_TEST_VAR_NAME, "empty")

    async with create_server_with_agent(self_registration_agent) as (server, test_client):
        yield server, test_client


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_self_registration_with_variables(
    self_registration_agent, get_final_task_from_stream, subtests, test_configuration
):
    os.environ.pop(SELF_REGISTRATION_TEST_VAR_NAME, None)
    _, client = self_registration_agent
    task = await get_final_task_from_stream(client.send_message(create_text_message_object(content="hi")))
    assert task.history[-1].parts[0].root.text == "empty"

    with subtests.test("register provider"):
        async for attempt in AsyncRetrying(stop=stop_after_delay(6), wait=wait_fixed(0.5), reraise=True):
            with attempt:
                providers = await Provider.list()
                assert len(providers) == 1, "Provider not registered"
                provider = providers[0]

        assert provider.state == "online"
        assert "self_registration_agent" in provider.source

    with subtests.test("update provider variables"):
        await provider.update_variables(variables={SELF_REGISTRATION_TEST_VAR_NAME: "test"})

        async for attempt in AsyncRetrying(stop=stop_after_delay(6), wait=wait_fixed(0.5), reraise=True):
            with attempt:
                task = await get_final_task_from_stream(client.send_message(create_text_message_object(content="hi")))
                assert task.history[-1].parts[0].root.text == "test"

    with subtests.test("remove provider variable"):
        await provider.update_variables(variables={SELF_REGISTRATION_TEST_VAR_NAME: None})

        async for attempt in AsyncRetrying(stop=stop_after_delay(6), wait=wait_fixed(0.5), reraise=True):
            with attempt:
                task = await get_final_task_from_stream(client.send_message(create_text_message_object(content="hi")))
                assert task.history[-1].parts[0].root.text == "empty"
