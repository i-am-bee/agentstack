# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions import LLMFulfillment, LLMServiceExtensionClient, LLMServiceExtensionSpec
from agentstack_sdk.platform import ModelProvider

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client", "setup_real_llm")
async def test_dependency_injection_example(
    subtests, get_final_task_from_stream, a2a_client_factory, test_configuration
):
    example_path = "agent-integration/overview/dependency-injection"

    async with run_example(example_path, a2a_client_factory) as running_example:
        spec = LLMServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)

        with subtests.test("agent reports LLM available when fulfillment provided"):
            metadata = LLMServiceExtensionClient(spec).fulfillment_metadata(
                llm_fulfillments={
                    "default": LLMFulfillment(
                        api_key=running_example.context_token.token.get_secret_value(),
                        api_model=(await ModelProvider.match())[0].model_id,
                        api_base="{platform_url}/api/v1/openai/",
                    )
                }
            )
            message = create_text_message_object(content="Hello")
            message.metadata = metadata
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "LLM service is available" in task.history[-1].parts[0].root.text

        with subtests.test("agent reports LLM not available without fulfillment"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "LLM service not available" in task.history[-1].parts[0].root.text
