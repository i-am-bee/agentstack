# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from beeai_sdk.platform import ModelProvider, SystemConfiguration

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_system_configuration(subtests, test_configuration):
    """Test system configuration get and update operations."""

    with subtests.test("get system configuration"):
        # Get current system configuration
        config = await SystemConfiguration.get()

        assert config is not None
        assert config.default_llm_model is None

    with subtests.test("update system configuration - llm model only"):
        # Update only the LLM model
        await ModelProvider.create(
            name="test_config",
            type=test_configuration.llm_provider_type,
            base_url=test_configuration.llm_api_base,
            api_key=test_configuration.llm_api_key.get_secret_value(),
        )
        updated_config = await SystemConfiguration.update(default_llm_model=test_configuration.llm_model)

        assert updated_config.default_llm_model == test_configuration.llm_model
        # Embedding model should remain unchanged
        assert updated_config.default_embedding_model is None
        assert updated_config.updated_at > config.updated_at

    with subtests.test("update system configuration - reset model"):
        updated_config = await SystemConfiguration.update(default_llm_model=None)
        assert updated_config.default_llm_model is None
