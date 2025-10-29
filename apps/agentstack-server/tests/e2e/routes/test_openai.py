# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import openai
import pytest
from agentstack_sdk.platform.context import Context, Permissions

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client", "setup_real_llm")
async def test_llm_permission_enforcement_with_context_token(subtests, test_configuration):
    """Test that LLM global permissions are properly enforced with context tokens."""
    base_url = test_configuration.server_url
    openai_base_url = f"{base_url}/api/v1/openai"
    test_message = {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}

    with subtests.test("LLM request denied with insufficient global permissions"):
        ctx = await Context.create()
        token = await ctx.generate_token(grant_global_permissions=Permissions(files={"read"}))
        openai_client = openai.AsyncOpenAI(api_key=token.token.get_secret_value(), base_url=openai_base_url)
        with pytest.raises(openai.PermissionDeniedError):
            resp = await openai_client.chat.completions.create(**test_message, model=test_configuration.llm_model)

    # Test with sufficient global permissions
    with subtests.test("LLM request succeeds with sufficient global permissions"):
        token = await ctx.generate_token(grant_global_permissions=Permissions(llm={"*"}))
        openai_client = openai.AsyncOpenAI(api_key=token.token.get_secret_value(), base_url=openai_base_url)
        resp = await openai_client.chat.completions.create(**test_message, model=test_configuration.llm_model)
        assert resp.choices[0].message.content


@pytest.mark.usefixtures("clean_up", "setup_platform_client", "setup_real_llm")
async def test_models_endpoint(subtests, test_configuration):
    """Test the /models endpoint returns available models including the default model."""
    base_url = test_configuration.server_url
    openai_base_url = f"{base_url}/api/v1/openai"

    with subtests.test("models endpoint returns default model"):
        # Create a context with LLM permissions to access models
        ctx = await Context.create()
        token = await ctx.generate_token(grant_global_permissions=Permissions(llm={"*"}, model_providers={"read"}))
        openai_client = openai.AsyncOpenAI(api_key=token.token.get_secret_value(), base_url=openai_base_url)

        # Get available models
        models = await openai_client.models.list()

        # Should have at least one model
        assert len(models.data) >= 1

        # The default model from test configuration should be in the list
        model_ids = [model.id for model in models.data]
        assert test_configuration.llm_model in model_ids
