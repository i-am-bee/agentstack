# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest

from agentstack_sdk.platform.client import PlatformClient

pytestmark = pytest.mark.unit


async def test_platform_client_reentrant():
    client = PlatformClient()
    async with client:
        async with client:
            async with client:
                assert client._ref_count == 3
            assert client._ref_count == 2
        assert client._ref_count == 1
        assert client.is_closed is False
    assert client._ref_count == 0
    assert client.is_closed
