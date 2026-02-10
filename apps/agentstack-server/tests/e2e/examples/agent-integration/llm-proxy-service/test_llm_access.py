# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions import LLMFulfillment, LLMServiceExtensionClient, LLMServiceExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_llm_access_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/llm-proxy-service/llm-access"

    async with run_example(example_path, a2a_client_factory) as running_example:
        spec = LLMServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)
        metadata = LLMServiceExtensionClient(spec).fulfillment_metadata(
            llm_fulfillments={
                "default": LLMFulfillment(
                    api_key=running_example.context_token.token.get_secret_value(),
                    api_model="ibm/granite-3-3-8b-instruct",
                    api_base="{platform_url}/api/v1/openai/",
                )
            }
        )

        with subtests.test("agent receives LLM configuration"):
            message = create_text_message_object(content="Hello")
            message.metadata = metadata
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "LLM access configured for model: ibm/granite-3-3-8b-instruct" in task.history[-1].parts[0].root.text
