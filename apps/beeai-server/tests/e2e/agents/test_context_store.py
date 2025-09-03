# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator, AsyncIterator

import pytest
from a2a.client import Client, ClientEvent, create_text_message_object
from a2a.types import Message, Role, Task
from beeai_sdk.a2a.extensions.services.platform import PlatformApiExtensionClient, PlatformApiExtensionSpec
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.platform.context import Context, ContextPermissions, ContextToken
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from beeai_sdk.server.store.platform_context_store import PlatformContextStore

pytestmark = pytest.mark.e2e


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task:
    final_task = None
    async for event in stream:
        match event:
            case (task, _):
                final_task = task
    return final_task


@pytest.fixture
async def history_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    """Agent that tests context.store.load_history() functionality."""

    async def history_agent(context: RunContext) -> AsyncGenerator[RunYield]:
        async for message in context.store.load_history():
            message.role = Role.agent
            yield message

    async with create_server_with_agent(history_agent, context_store=PlatformContextStore()) as (server, client):
        yield server, client


def create_message(token: ContextToken, content: str) -> Message:
    api_extension_client = PlatformApiExtensionClient(PlatformApiExtensionSpec())
    message = create_text_message_object(content=content)
    message.metadata = api_extension_client.api_auth_metadata(auth_token=token.token, expires_at=token.expires_at)
    message.context_id = token.context_id
    return message


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_agent_history(history_agent, subtests):
    server, client = history_agent

    with subtests.test("history repeats itself"):
        context1 = await Context.create()
        token = await context1.generate_token(grant_context_permissions=ContextPermissions(context_data={"*"}))

        final_task = await get_final_task_from_stream(client.send_message(create_message(token, "first message")))
        agent_messages = [msg.parts[0].root.text for msg in final_task.history]
        assert agent_messages == ["first message"]

        final_task = await get_final_task_from_stream(client.send_message(create_message(token, "second message")))
        agent_messages = [msg.parts[0].root.text for msg in final_task.history]
        assert agent_messages == ["first message", "first message", "second message"]

        final_task = await get_final_task_from_stream(client.send_message(create_message(token, "third message")))
        agent_messages = [msg.parts[0].root.text for msg in final_task.history]
        assert agent_messages == [
            # first run
            "first message",
            # second run
            "first message",
            "second message",
            # third run
            "first message",
            "first message",
            "second message",
            "third message",
        ]

        context1_history = await Context.list_history(context1.id)
        assert len(context1_history) == 14

    with subtests.test("other context id does not mix history"):
        context2 = await Context.create()
        token = await context2.generate_token(grant_context_permissions=ContextPermissions(context_data={"*"}))
        final_task = await get_final_task_from_stream(client.send_message(create_message(token, "first message")))
        agent_messages = [msg.parts[0].root.text for msg in final_task.history]
        assert agent_messages == ["first message"]

        context1_history = await Context.list_history(context1.id)
        assert len(context1_history) == 14

        context2_history = await Context.list_history(context2.id)
        assert len(context2_history) == 2
