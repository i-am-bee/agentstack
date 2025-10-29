# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging

import pytest
from a2a.types import AgentCapabilities, AgentCard
from agentstack_sdk.platform import Provider
from httpx import HTTPError

pytestmark = pytest.mark.e2e

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_provider_crud(subtests, test_configuration):
    with subtests.test("add provider"):
        variables = {"test": "var"}
        provider = await Provider.create(location=test_configuration.test_agent_image, variables=variables)
        assert await provider.list_variables() == variables

    with subtests.test("patch provider"):
        new_source = test_configuration.test_agent_image
        new_agent_card = AgentCard(
            name="test",
            description="test",
            url="http://localhost:8000/",
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(),
            skills=[],
        )
        provider = await provider.patch(location=new_source, agent_card=new_agent_card)
        assert provider.agent_card.name == new_agent_card.name
        assert provider.source == new_source
        assert await provider.list_variables() == variables  # variables haven't changed

    with subtests.test("change provider variables"):
        new_variables = {"other": "var"}
        provider = await provider.patch(variables=new_variables)
        assert await provider.list_variables() == new_variables

        provider = await provider.patch(variables={})
        assert await provider.list_variables() == {}

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
