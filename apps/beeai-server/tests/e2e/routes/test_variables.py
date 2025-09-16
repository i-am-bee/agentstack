# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from beeai_sdk.platform.variables import Variables

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_user_variables(subtests):
    """Test user-scoped variables operations using the SDK Variables class."""

    test_variables = {"USER_VAR_1": "value1", "USER_VAR_2": "value2", "API_TOKEN": "secret-token-456"}

    with subtests.test("save user variables"):
        # Test saving variables using the Variables class
        variables = Variables(test_variables)
        await variables.save()

    with subtests.test("load user variables"):
        # Test loading variables into a new Variables instance
        loaded_variables = await Variables().load()

        assert len(loaded_variables) == len(test_variables)
        for key, value in test_variables.items():
            assert loaded_variables[key] == value

    with subtests.test("update specific user variables"):
        # Test partial updates
        partial_update = {"USER_VAR_1": "updated_value1", "NEW_VAR": "new_value"}

        await Variables(partial_update).save()

        # Check the updated variables
        variables = await Variables().load()

        # Should have the updated and new values
        assert variables["USER_VAR_1"] == "updated_value1"
        assert variables["NEW_VAR"] == "new_value"
        # Previous variables should still be there
        assert variables["USER_VAR_2"] == "value2"
        assert variables["API_TOKEN"] == "secret-token-456"
        assert len(variables) == 4

    with subtests.test("remove user variables"):
        # Load existing variables, set some to None, then save
        variables = await Variables().load()
        variables["USER_VAR_2"] = None
        variables["API_TOKEN"] = None
        await variables.save()

        # Reload and verify removal
        variables = await Variables().load()

        assert len(variables) == 2
        assert "USER_VAR_1" in variables
        assert "NEW_VAR" in variables
        assert "USER_VAR_2" not in variables
        assert "API_TOKEN" not in variables

    with subtests.test("clear all variables"):
        # Load all variables, set them to None, then save
        variables = await Variables().load()
        for key in list(variables.keys()):
            variables[key] = None
        await variables.save()

        # Should have no variables
        variables = await Variables().load()
        assert len(variables) == 0
