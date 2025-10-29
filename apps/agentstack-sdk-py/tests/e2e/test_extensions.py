# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from random import random
from typing import Annotated

import pytest
from a2a.client import Client, ClientEvent
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, Task

from agentstack_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from agentstack_sdk.a2a.extensions.services.llm import LLMFulfillment, LLMServiceExtensionClient
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server

pytestmark = pytest.mark.e2e


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task:
    final_task = None
    async for event in stream:
        match event:
            case (task, _):
                final_task = task
    return final_task


@pytest.fixture
async def llm_extension_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def chunked_artifact_producer(
        llm_ext: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
    ) -> AsyncGenerator[RunYield, Message]:
        # Agent producing chunked artifacts
        await asyncio.sleep(random() * 0.5)
        api_key = next(iter(llm_ext.data.llm_fulfillments.values())).api_key
        yield api_key

    async with create_server_with_agent(chunked_artifact_producer) as (server, test_client):
        yield server, test_client


async def test_extension_is_not_reused(llm_extension_agent):
    _, client = llm_extension_agent
    card = await client.get_card()
    llm_spec = LLMServiceExtensionSpec.from_agent_card(card)
    extension_client = LLMServiceExtensionClient(llm_spec)

    tasks = []

    for i in range(10):
        message = create_text_message_object()
        message.metadata = extension_client.fulfillment_metadata(
            llm_fulfillments={"default": LLMFulfillment(api_key=str(i), api_model="model", api_base="base")}
        )
        tasks.append(asyncio.create_task(get_final_task_from_stream(client.send_message(message))))

    results = await asyncio.gather(*tasks)
    for i, task in enumerate(results):
        assert task.history[-1].parts[0].root.text == str(i)
