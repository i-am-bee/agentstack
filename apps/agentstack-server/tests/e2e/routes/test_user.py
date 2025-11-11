# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from agentstack_sdk.platform.user import User

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("setup_platform_client")
async def test_get_user():
    user = await User.get()
    assert user.email == "admin@beeai.dev"
    assert user.role == "admin"
