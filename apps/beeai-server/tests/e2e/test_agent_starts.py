import asyncio

import pytest
from acp_sdk import MessagePart


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_agent(subtests, setup_real_llm, api_client, acp_client):
    agent_image = "ghcr.io/i-am-bee/beeai-platform/official/beeai-framework/chat:agents-v0.2.14"
    with subtests.test("add chat agent"):
        response = await api_client.post("providers", json={"location": agent_image})
        response.raise_for_status()
        providers_response = await api_client.get("providers")
        providers_response.raise_for_status()
        providers = providers_response.json()
        assert len(providers["items"]) == 1
        assert providers["items"][0]["source"] == agent_image

    with subtests.test("run chat agent for the first time"):
        num_parallel = 3
        agent_input = MessagePart(content="Repeat this exactly: 'hello world'", role="user")

        # Run 3 requests in parallel (test that each request waits)
        run_results = await asyncio.gather(
            *(acp_client.run_sync(agent_input, agent="chat") for _ in range(num_parallel))
        )

        for result in run_results:
            assert not result.error
            assert "hello" in str(result.output[0]).lower()

    with subtests.test("run chat agent for the second time"):
        run = await acp_client.run_sync(agent_input, agent="chat")
        assert not run.error
        assert "hello" in str(run.output[0]).lower()
