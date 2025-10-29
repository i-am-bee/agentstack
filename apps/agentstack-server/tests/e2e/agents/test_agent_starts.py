# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    Role,
    Task,
    TaskState,
)
from agentstack_sdk.a2a.extensions import (
    LLMFulfillment,
    LLMServiceExtensionClient,
    LLMServiceExtensionSpec,
    PlatformApiExtensionClient,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.platform import ModelProvider, Provider
from agentstack_sdk.platform.context import Context, ContextPermissions, Permissions

pytestmark = pytest.mark.e2e


def extract_agent_text_from_stream(task: Task) -> str:
    assert task.history
    return "".join(item.parts[0].root.text for item in task.history if item.role == Role.agent if item.parts)


@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_remote_agent(subtests, a2a_client_factory, get_final_task_from_stream, test_configuration):
    agent_image = test_configuration.test_agent_image
    with subtests.test("add chat agent"):
        _ = await Provider.create(location=agent_image)
        providers = await Provider.list()
        context = await Context.create()
        context_token = await context.generate_token(
            grant_global_permissions=Permissions(llm={"*"}),
            grant_context_permissions=ContextPermissions(context_data={"*"}),
        )
        assert len(providers) == 1
        assert providers[0].source == agent_image
        assert providers[0].agent_card

        async with a2a_client_factory(providers[0].agent_card) as a2a_client:
            with subtests.test("run chat agent for the first time"):
                num_parallel = 3
                message = create_text_message_object(
                    content="Repeat this exactly, use the act tool with final_answer: 'hello world'"
                )
                spec = LLMServiceExtensionSpec.from_agent_card(providers[0].agent_card)
                platform_api_spec = PlatformApiExtensionSpec.from_agent_card(providers[0].agent_card)
                message.metadata = LLMServiceExtensionClient(spec).fulfillment_metadata(
                    llm_fulfillments={
                        "default": LLMFulfillment(
                            api_key=context_token.token.get_secret_value(),
                            api_model=(await ModelProvider.match())[0].model_id,
                            api_base="{platform_url}/api/v1/openai/",
                        )
                    }
                ) | PlatformApiExtensionClient(platform_api_spec).api_auth_metadata(
                    auth_token=context_token.token,
                    expires_at=context_token.expires_at,
                )
                message.context_id = context.id
                task = await get_final_task_from_stream(a2a_client.send_message(message))

                # Verify response
                assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
                assert "hello world" in extract_agent_text_from_stream(task)

                # Run 3 requests in parallel (test that each request waits)
                run_results = await asyncio.gather(
                    *(get_final_task_from_stream(a2a_client.send_message(message)) for _ in range(num_parallel))
                )

                for task in run_results:
                    assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
                    assert "hello world" in extract_agent_text_from_stream(task)

            with subtests.test("run chat agent for the second time"):
                task = await get_final_task_from_stream(a2a_client.send_message(message))
                assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
                assert "hello world" in extract_agent_text_from_stream(task)
