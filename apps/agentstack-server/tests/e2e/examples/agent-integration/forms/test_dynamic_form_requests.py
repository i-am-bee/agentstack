# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import uuid4

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, Role, TaskState
from agentstack_sdk.a2a.extensions.common.form import FormResponse, TextFieldValue
from agentstack_sdk.a2a.extensions.ui.form_request import FormRequestExtensionClient, FormRequestExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_dynamic_form_requests_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/forms/dynamic-form-requests"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent requests form and processes submitted data"):
            # Send message that triggers form request
            message = create_text_message_object(content="I'd like you to contact me")
            message.context_id = running_example.context.id

            # Get the task - should be in input_required state with form
            task = await get_final_task_from_stream(running_example.client.send_message(message))
            assert task.status.state == TaskState.input_required

            # Parse the form request from the task status message
            spec = FormRequestExtensionSpec()
            client = FormRequestExtensionClient(spec)
            form_render = client.parse_server_metadata(task.status.message)
            assert form_render is not None
            assert form_render.title == "Please provide your contact information"

            # Send form response
            form_response = FormResponse(
                values={
                    "email": TextFieldValue(value="test@example.com"),
                    "phone": TextFieldValue(value="555-1234"),
                    "company": TextFieldValue(value="Acme Corp"),
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

            # Send the form response and get final task
            final_task = await get_final_task_from_stream(running_example.client.send_message(response_message))

            assert final_task.status.state == TaskState.completed, (
                f"Fail: {final_task.status.message.parts[0].root.text}"
            )
            assert "test@example.com" in final_task.history[-1].parts[0].root.text
            assert "555-1234" in final_task.history[-1].parts[0].root.text
            assert "Acme Corp" in final_task.history[-1].parts[0].root.text
