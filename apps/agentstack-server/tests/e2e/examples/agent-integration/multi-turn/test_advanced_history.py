# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions import LLMFulfillment, LLMServiceExtensionClient, LLMServiceExtensionSpec
from agentstack_sdk.platform import ModelProvider

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_advanced_history_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/multi-turn/advanced-history"

    async with run_example(example_path, a2a_client_factory) as running_example:
        spec = LLMServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)
        metadata = LLMServiceExtensionClient(spec).fulfillment_metadata(
            llm_fulfillments={
                "default": LLMFulfillment(
                    api_key=running_example.context_token.token.get_secret_value(),
                    api_model=(await ModelProvider.match())[0].model_id,
                    api_base="{platform_url}/api/v1/openai/",
                )
            }
        )

        with subtests.test("agent responds with a greeting"):
            message = create_text_message_object(content=("Hi, my name is John. How are you?"))
            message.metadata = metadata
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert any(sub in task.history[-1].parts[0].root.text.lower() for sub in ["hello", "hi"])

        with subtests.test("agent remembers user name from history"):
            message = create_text_message_object(content="Can you remind me my name?")
            message.metadata = metadata
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "john" in task.history[-1].parts[0].root.text.lower()
