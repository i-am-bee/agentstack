# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions.ui.canvas import CanvasExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_canvas_with_llm_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/canvas/canvas-with-llm"

    async with run_example(example_path, a2a_client_factory) as running_example:
        canvas_uri = CanvasExtensionSpec.URI

        with subtests.test("agent generates code artifact"):
            message = create_text_message_object(content="Write a hello world program")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

            # Verify artifact is returned (the agent uses a mocked LLM response)
            assert len(task.artifacts) > 0
            artifact = task.artifacts[0]
            assert artifact.name == "Response"

            # Verify the artifact contains the expected mock response
            artifact_text = "".join(part.root.text for part in artifact.parts if hasattr(part.root, "text"))
            assert "Hello from LLM!" in artifact_text

        with subtests.test("agent updates artifact via canvas edit"):
            # Use the artifact from the previous test
            artifact_id = artifact.artifact_id

            # Get the artifact text to determine indices
            artifact_text = "".join(part.root.text for part in artifact.parts if hasattr(part.root, "text"))

            # Send edit request for a portion of the code
            message = create_text_message_object(content="Change print to use f-string")
            message.context_id = running_example.context.id
            message.metadata = {
                canvas_uri: {
                    "artifact_id": artifact_id,
                    "start_index": 0,
                    "end_index": min(50, len(artifact_text)),  # Select first 50 chars
                    "description": "Change print to use f-string",
                }
            }
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

            # Verify updated artifact is returned
            assert len(task.artifacts) > 0
            updated_artifact = task.artifacts[0]

            # Verify the response contains the edit prompt context
            updated_text = "".join(part.root.text for part in updated_artifact.parts if hasattr(part.root, "text"))
            assert "editing existing code" in updated_text.lower() or "selected" in updated_text.lower()
