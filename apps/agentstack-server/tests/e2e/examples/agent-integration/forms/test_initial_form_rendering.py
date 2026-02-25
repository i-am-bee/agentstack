# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions import FormResponse, FormServiceExtensionMetadata, FormServiceExtensionSpec
from agentstack_sdk.a2a.extensions.common.form import TextFieldValue

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_initial_form_rendering_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/forms/initial-form-rendering"

    async with run_example(example_path, a2a_client_factory) as running_example:
        spec = FormServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)
        assert spec is not None, "FormServiceExtensionSpec should be present in agent card"
        with subtests.test("agent responds with greeting using form data"):
            message = create_text_message_object()
            metadata = FormServiceExtensionMetadata(
                form_fulfillments={
                    "initial_form": FormResponse(
                        values={"first_name": TextFieldValue(value="Alice"), "last_name": TextFieldValue(value="Smith")}
                    )
                }
            ).model_dump(mode="json")

            message.metadata = {spec.URI: metadata}
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "Hello Alice Smith! Nice to meet you." in task.history[-1].parts[0].root.text
