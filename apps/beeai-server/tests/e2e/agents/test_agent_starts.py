# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from uuid import uuid4

import pytest
from a2a.types import (
    Message,
    Part,
    Role,
    TaskState,
    TextPart,
)
from beeai_sdk.platform import Provider


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.skip("TODO: temporary skip until beeai-sdk with 0.3.0 is at least merged to main")
@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_agent(subtests, a2a_client_factory, get_final_task_from_stream):
    agent_image = "ghcr.io/i-am-bee/beeai-platform-agent-starter/my-agent-a2a:latest"
    with subtests.test("add chat agent"):
        _ = await Provider.create(location=agent_image)
        providers = await Provider.list()
        assert len(providers) == 1
        assert providers[0].source == agent_image
        assert providers[0].agent_card

        async with a2a_client_factory(providers[0].agent_card) as a2a_client:
            with subtests.test("run chat agent for the first time"):
                num_parallel = 3
                message = Message(
                    message_id=str(uuid4()),
                    parts=[Part(root=TextPart(text="Repeat this exactly: 'hello world'"))],
                    role=Role.user,
                )
                response = await get_final_task_from_stream(a2a_client.send_message(message))

                # Verify response
                assert response.status.state == TaskState.completed
                assert "hello world" in response.history[-1].parts[0].root.text

                # Run 3 requests in parallel (test that each request waits)
                run_results = await asyncio.gather(
                    *(get_final_task_from_stream(a2a_client.send_message(message)) for _ in range(num_parallel))
                )

                for response in run_results:
                    assert response.status.state == TaskState.completed
                    assert "hello world" in response.history[-1].parts[0].root.text

            with subtests.test("run chat agent for the second time"):
                response = await get_final_task_from_stream(a2a_client.send_message(message))
                assert response.status.state == TaskState.completed
                assert "hello world" in response.history[-1].parts[0].root.text
