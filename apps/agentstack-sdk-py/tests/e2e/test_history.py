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

from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.memory_context_store import InMemoryContextStore

pytestmark = pytest.mark.e2e


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task | None:
    final_task = None
    async for event in stream:
        match event:
            case (task, _):
                final_task = task
    return final_task


async def send_message_get_response(
    client: Client, content: str, context_id: str | None = None
) -> tuple[list[str], str]:
    message = create_text_message_object(content=content)
    if context_id is not None:
        message.context_id = context_id
    final_task = await get_final_task_from_stream(client.send_message(message))

    agent_messages = [msg.parts[0].root.text for msg in final_task.history or []]
    return agent_messages, final_task.context_id


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


@pytest.fixture
async def history_deleting_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    """Agent that tests context.store.load_history() functionality."""
    context_store = InMemoryContextStore()

    async def history_agent(input: Message, context: RunContext) -> AsyncGenerator[RunYield, None]:
        await context.store(input)
        n_messages = 0
        async for message in context.load_history(load_history_items=True):
            n_messages += 1
            if n_messages == 1:
                delete_id = message.id
            if n_messages > 3:
                # pyrefly: ignore [unbound-name]
                await context.delete_history_from_id(delete_id)
                break

        async for message in context.load_history():
            message.role = Role.agent
            yield message

    async with create_server_with_agent(history_agent, context_store=context_store) as (server, client):
        yield server, client


async def test_agent_history(history_agent):
    """Test that history starts empty."""
    _, client = history_agent

    agent_messages, context_id = await send_message_get_response(client, "first message")
    assert agent_messages == ["first message"]

    agent_messages, context_id = await send_message_get_response(client, "second message", context_id=context_id)
    assert agent_messages == ["first message", "first message", "second message"]

    agent_messages, context_id = await send_message_get_response(client, "third message", context_id=context_id)
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


async def test_agent_deleting_history(history_deleting_agent):
    """Test that history starts empty."""
    _, client = history_deleting_agent

    agent_messages, context_id = await send_message_get_response(client, "first message")
    assert agent_messages == ["first message"]

    agent_messages, context_id = await send_message_get_response(client, "second message", context_id=context_id)
    assert agent_messages == ["first message", "second message"]

    agent_messages, context_id = await send_message_get_response(client, "third message", context_id=context_id)
    assert agent_messages == ["first message", "second message", "third message"]

    agent_messages, context_id = await send_message_get_response(client, "delete message", context_id=context_id)
    assert agent_messages == []

    agent_messages, context_id = await send_message_get_response(client, "first message")
    assert agent_messages == ["first message"]
