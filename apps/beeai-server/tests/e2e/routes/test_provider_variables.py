# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.types import AgentCapabilities, AgentCard
from beeai_sdk.platform import Provider

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_provider_variables(subtests):
    """Test provider environment variables operations."""

    # First create a real test provider
    provider = await Provider.create(
        location="ghcr.io/test-image:0.0.1",
        agent_card=AgentCard(
            capabilities=AgentCapabilities(),
            default_input_modes=[],
            default_output_modes=[],
            name="test_agent",
            skills=[],
            description="test agent",
            url="http://localhost:8000",
            version="0.0.1",
        ),
    )
    provider_id = provider.id

    test_variables = {"TEST_VAR_1": "value1", "TEST_VAR_2": "value2", "API_KEY": "secret-key-123"}

    with subtests.test("update provider variables"):
        await provider.update_variables(variables=test_variables)

    with subtests.test("list provider variables"):
        variables = await provider.list_variables()

        assert len(variables) == len(test_variables)
        for key, value in test_variables.items():
            assert variables[key] == value

    with subtests.test("update specific provider variables"):
        partial_update = {"TEST_VAR_1": "updated_value1", "NEW_VAR": "new_value"}

        await provider.update_variables(variables=partial_update)

        # Check the updated variables
        variables = await provider.list_variables()

        # Should have the updated and new values
        assert variables["TEST_VAR_1"] == "updated_value1"
        assert variables["NEW_VAR"] == "new_value"
        # Previous variables should still be there
        assert variables["TEST_VAR_2"] == "value2"
        assert variables["API_KEY"] == "secret-key-123"
        assert len(variables) == 4

    with subtests.test("remove provider variables"):
        # Remove a variable by setting it to None
        remove_update = {"TEST_VAR_2": None, "API_KEY": None}

        await provider.update_variables(variables=remove_update)

        variables = await provider.list_variables()

        assert len(variables) == 2
        assert "TEST_VAR_1" in variables
        assert "NEW_VAR" in variables
        assert "TEST_VAR_2" not in variables
        assert "API_KEY" not in variables

    with subtests.test("empty variables list"):
        # Remove all remaining variables
        clear_update = {"TEST_VAR_1": None, "NEW_VAR": None}

        await provider.update_variables(variables=clear_update)

        # Should have no variables
        variables = await Provider.list_variables(provider_id)
        assert len(variables) == 0
