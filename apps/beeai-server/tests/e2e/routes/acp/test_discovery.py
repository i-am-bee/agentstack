import pytest
from acp_sdk.client import Client
from acp_sdk.models import AgentManifest
from acp_sdk.server import Server
from acp_sdk.models.platform import PlatformUIType, AgentToolInfo


"""
These tests are copied from acp repository: 
https://github.com/i-am-bee/acp/blob/main/python/tests/e2e/test_suites/test_discovery.py
"""

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_ping(server: Server, acp_client: Client) -> None:
    await acp_client.ping()
    assert True


@pytest.mark.asyncio
async def test_agents_list(server: Server, acp_client: Client) -> None:
    async for agent in acp_client.agents():
        assert isinstance(agent, AgentManifest)


@pytest.mark.asyncio
async def test_agents_manifest(server: Server, acp_client: Client) -> None:
    agent_name = "echo"
    agent = await acp_client.agent(name=agent_name)
    assert isinstance(agent, AgentManifest)
    assert agent.name == agent_name


@pytest.mark.asyncio
async def test_platform_annotations(server: Server, acp_client: Client) -> None:
    agent_name = "platform_annotations"
    agent = await acp_client.agent(name=agent_name)
    assert isinstance(agent, AgentManifest)
    assert agent.name == agent_name
    assert agent.metadata.annotations.beeai_ui.user_greeting == "This is a test"
    assert agent.metadata.annotations.beeai_ui.ui_type == PlatformUIType.HANDSOFF
    assert agent.metadata.annotations.beeai_ui.tools == [
        AgentToolInfo(name="testing tool", description="testing description")
    ]
