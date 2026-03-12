# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging

import pytest
from a2a.types import AgentCapabilities, AgentCard
from agentstack_sdk.platform import Provider
from httpx import HTTPError

pytestmark = pytest.mark.e2e

logger = logging.getLogger(__name__)

TEST_AGENT_CARD = AgentCard(
    name="TestAgent",
    description="A test agent",
    url="http://test-agent.example.com:8000/",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(),
    skills=[],
)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_provider_crud(subtests):
    with subtests.test("add provider"):
        provider = await Provider.create(
            location="http://test-agent.example.com:8000",
            agent_card=TEST_AGENT_CARD,
        )
        assert provider.agent_card.name == "TestAgent"
        assert provider.source_type == "api"

    with subtests.test("test user_owned filtering"):
        # Test user_owned=True (should see exactly 1 provider - admin's)
        admin_providers = await Provider.list(user_owned=True)
        assert len(admin_providers) == 1
        assert admin_providers[0].id == provider.id

        # Test user_owned=False (should see 0 providers - no other users' providers)
        others_providers = await Provider.list(user_owned=False)
        assert len(others_providers) == 0

        # Test user_owned=None (should see exactly 1 provider - all providers)
        all_providers = await Provider.list(user_owned=None)
        assert len(all_providers) == 1
        assert all_providers[0].id == provider.id

    with subtests.test("delete provider"):
        await provider.delete()
        with pytest.raises(HTTPError, match="404 Not Found"):
            await provider.get()
