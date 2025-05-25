import pytest
from acp_sdk import MessagePart


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_agent(subtests, setup_real_llm, api_client, acp_client):
    agent_image = "ghcr.io/i-am-bee/beeai-platform/official/beeai-framework/chat:agents-v0.1.3"
    with subtests.test("add chat agent"):
        async with api_client() as client:
            response = await client.post("providers", json={"location": agent_image})
            response.raise_for_status()
            providers_response = await client.get("providers")
            providers_response.raise_for_status()
            providers = providers_response.json()
            assert len(providers["items"]) == 1
            assert providers["items"][0]["source"] == agent_image

    agent_input = MessagePart(content="Repeat this exactly: 'hello world'", role="user")
    with subtests.test("run chat agent for the first time"):
        async with acp_client() as client:
            run = await client.run_sync(agent_input, agent="chat")
            assert not run.error
            assert "hello" in str(run.output[0]).lower()

    with subtests.test("run chat agent for the second time"):
        async with acp_client() as client:
            run = await client.run_sync(agent_input, agent="chat")
            assert not run.error
            assert "hello" in str(run.output[0]).lower()
