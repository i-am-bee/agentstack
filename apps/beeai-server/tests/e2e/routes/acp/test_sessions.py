# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio

import pytest
from acp_sdk import Message, MessagePart, Session
from acp_sdk.client import Client
from acp_sdk.server import Server

"""
These tests are copied from acp repository: 
https://github.com/i-am-bee/acp/blob/main/python/tests/e2e/test_suites/test_sessions.py
"""

pytestmark = pytest.mark.e2e

agent = "history_echo"
input = [Message(parts=[MessagePart(content="Hello!")])]
output = [message.model_copy(update={"role": f"agent/{agent}"}) for message in input]


@pytest.mark.asyncio
async def test_session(server: Server, acp_client: Client) -> None:
    async with acp_client.session() as session:
        run = await session.run_sync(agent=agent, input=input)
        assert run.output == output
        run = await session.run_sync(agent=agent, input=input)
        assert run.output == output * 3


@pytest.mark.asyncio
@pytest.mark.skip(reason="Waiting for header implementation in acp-sdk")
async def test_session_refresh(server: Server, acp_client: Client) -> None:
    async with acp_client.session() as session:
        await session.run_async(agent=agent, input=input)
        await asyncio.sleep(2)
        sess = await session.refresh_session()
        assert len(sess.history) == len(input) * 2


@pytest.mark.asyncio
@pytest.mark.skip(reason="Waiting for header implementation in acp-sdk")
async def test_session_multi_client(server: Server, acp_client: Client) -> None:
    session = Session()

    async with acp_client.session(session) as session_client:
        run = await session_client.run_sync(input, agent=agent)
        assert run.output == output
        print(run.session_id)

    async with acp_client.session(session) as session_client:
        run = await session_client.run_sync(input, agent=agent)
        assert run.output == output * 3
