# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from uuid import uuid4

import pytest
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Role,
    SendMessageRequest,
    SendMessageSuccessResponse,
    TextPart,
)


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_agent(subtests, setup_real_llm, api_client, a2a_client_factory):
    agent_image = "ghcr.io/i-am-bee/beeai-platform-agent-starter/my-agent-a2a:latest"
    with subtests.test("add chat agent"):
        response = await api_client.post("providers", json={"location": agent_image})
        response.raise_for_status()
        providers_response = await api_client.get("providers")
        providers_response.raise_for_status()
        providers = providers_response.json()
        assert len(providers["items"]) == 1
        assert providers["items"][0]["source"] == agent_image
        agent_card = AgentCard.model_validate(providers["items"][0]["agent_card"])
        assert agent_card

        async with a2a_client_factory(agent_card) as a2a_client:
            with subtests.test("run chat agent for the first time"):
                num_parallel = 3
                message = Message(
                    messageId=str(uuid4()), parts=[TextPart(text="Repeat this exactly: 'hello world'")], role=Role.user
                )
                response = await a2a_client.send_message(
                    SendMessageRequest(id=str(uuid4()), params=MessageSendParams(message=message))
                )

                # Verify response
                assert isinstance(response.root, SendMessageSuccessResponse)
                assert "hello world" in response.root.result.parts[0].root.text

                # Run 3 requests in parallel (test that each request waits)
                run_results = await asyncio.gather(
                    *(
                        a2a_client.send_message(
                            SendMessageRequest(id=str(uuid4()), params=MessageSendParams(message=message))
                        )
                        for _ in range(num_parallel)
                    )
                )

                for response in run_results:
                    assert isinstance(response.root, SendMessageSuccessResponse)
                    assert "hello world" in response.root.result.parts[0].root.text

            with subtests.test("run chat agent for the second time"):
                response = await a2a_client.send_message(
                    SendMessageRequest(id=str(uuid4()), params=MessageSendParams(message=message))
                )
                assert isinstance(response.root, SendMessageSuccessResponse)
                assert "hello world" in response.root.result.parts[0].root.text
