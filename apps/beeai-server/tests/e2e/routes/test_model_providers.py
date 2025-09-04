# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from beeai_sdk.platform import ModelProvider

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up", "setup_platform_client", "setup_real_llm")
async def test_setup_real_llm_creates_provider():
    """Test that setup_real_llm fixture creates at least one model provider."""
    providers = await ModelProvider.list()

    # The setup_real_llm fixture should create at least one provider
    assert len(providers) >= 1

    # Verify the provider has expected properties
    provider = providers[0]
    assert provider.id is not None
    assert provider.type is not None
    assert provider.base_url is not None
    assert provider.created_at is not None
