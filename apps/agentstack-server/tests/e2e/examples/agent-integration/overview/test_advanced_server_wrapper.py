# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, Role, TaskState
from agentstack_sdk.a2a.extensions.common.form import FormResponse, TextFieldValue
from agentstack_sdk.a2a.extensions.ui.form_request import FormRequestExtensionClient, FormRequestExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_advanced_server_wrapper_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/overview/advanced-server-wrapper"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent requests form and responds with submitted data"):
            # Send initial message - agent should pause and request a form
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id

            task = await get_final_task_from_stream(running_example.client.send_message(message))
            assert task.status.state == TaskState.input_required

            # Parse the form request from the task status message
            spec = FormRequestExtensionSpec()
            client = FormRequestExtensionClient(spec)
            form_render = client.parse_server_metadata(task.status.message)
            assert form_render is not None
            assert form_render.title == "Please provide your details"

            # Submit form response with name and email
            form_response = FormResponse(
                values={
                    "name": TextFieldValue(value="Alice"),
                    "email": TextFieldValue(value="alice@example.com"),
                }
            )
            response_message = Message(
                role=Role.user,
                message_id=str(uuid4()),
                task_id=task.id,
                context_id=running_example.context.id,
                parts=[],
                metadata={spec.URI: form_response.model_dump(mode="json")},
            )

            # Send form response and verify final task
            final_task = await get_final_task_from_stream(running_example.client.send_message(response_message))

            assert final_task.status.state == TaskState.completed, (
                f"Fail: {final_task.status.message.parts[0].root.text}"
            )
            assert "Alice" in final_task.history[-1].parts[0].root.text
            assert "alice@example.com" in final_task.history[-1].parts[0].root.text
