# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions import FormServiceExtensionMetadata, FormServiceExtensionSpec, SettingsFormResponse
from agentstack_sdk.a2a.extensions.common.form import CheckboxGroupFieldValue, SingleSelectFieldValue

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_settings_form_rendering_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/forms/settings-form-rendering"

    async with run_example(example_path, a2a_client_factory) as running_example:
        spec = FormServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)
        assert spec is not None, "FormServiceExtensionSpec should be present in agent card"
        with subtests.test("agent responds with greeting using form data"):
            message = create_text_message_object(content="Show me the settings")
            metadata = FormServiceExtensionMetadata(
                form_fulfillments={
                    "settings_form": SettingsFormResponse(
                        values={
                            "checkbox_settings": CheckboxGroupFieldValue(value={"thinking": True, "memory": False}),
                            "response_style": SingleSelectFieldValue(value="humorous"),
                        }
                    )
                }
            ).model_dump(mode="json")

            message.metadata = {spec.URI: metadata}
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "Thinking is enabled" in task.history[-1].parts[0].root.text
            assert "Memory is disabled" in task.history[-1].parts[0].root.text
            assert "Response style: humorous" in task.history[-1].parts[0].root.text
