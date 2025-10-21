# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator, AsyncIterator

import pytest
from a2a.client import Client, ClientEvent, create_text_message_object
from a2a.types import (
    Message,
    Role,
    Task,
)

from beeai_sdk.a2a.types import RunYield
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from beeai_sdk.server.store.memory_context_store import InMemoryContextStore

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
    context_store = InMemoryContextStore()

    async def history_agent(input: Message, context: RunContext) -> AsyncGenerator[RunYield, None]:
        await context.store(input)
        async for message in context.load_history():
            message.role = Role.agent
            yield message
            await context.store(message)

    async with create_server_with_agent(history_agent, context_store=context_store) as (server, client):
        yield server, client


async def test_agent_history(history_agent):
    """Test that history starts empty."""
    _, client = history_agent
    message = create_text_message_object(content="first message")

    final_task = await get_final_task_from_stream(client.send_message(message))
    agent_messages = [msg.parts[0].root.text for msg in final_task.history]
    assert agent_messages == ["first message"]

    message = create_text_message_object(content="second message")
    message.context_id = final_task.context_id
    final_task = await get_final_task_from_stream(client.send_message(message))
    agent_messages = [msg.parts[0].root.text for msg in final_task.history]
    assert agent_messages == ["first message", "first message", "second message"]

    message = create_text_message_object(content="third message")
    message.context_id = final_task.context_id
    final_task = await get_final_task_from_stream(client.send_message(message))
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
