# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import openai
import pytest
from beeai_sdk.platform.context import Context, Permissions

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client", "setup_real_llm")
async def test_llm_permission_enforcement_with_context_token(subtests, test_configuration):
    """Test that LLM global permissions are properly enforced with context tokens."""
    base_url = test_configuration.server_url
    openai_base_url = f"{base_url}/api/v1/llm"
    test_message = {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}

    with subtests.test("LLM request denied with insufficient global permissions"):
        ctx = await Context.create()
        token = await ctx.generate_token(grant_global_permissions=Permissions(files={"read"}))
        openai_client = openai.AsyncOpenAI(api_key=token.token.get_secret_value(), base_url=openai_base_url)
        with pytest.raises(openai.PermissionDeniedError):
            resp = await openai_client.chat.completions.create(**test_message, model="dummy")

    # Test with sufficient global permissions
    with subtests.test("LLM request succeeds with sufficient global permissions"):
        token = await ctx.generate_token(grant_global_permissions=Permissions(llm={"*"}))
        openai_client = openai.AsyncOpenAI(api_key=token.token.get_secret_value(), base_url=openai_base_url)
        resp = await openai_client.chat.completions.create(**test_message, model="dummy")
        assert resp.choices[0].message.content
