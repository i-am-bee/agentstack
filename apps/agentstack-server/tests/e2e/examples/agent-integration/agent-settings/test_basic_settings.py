# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions.ui.settings import SettingsExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_basic_settings_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/agent-settings/basic-settings"

    async with run_example(example_path, a2a_client_factory) as running_example:
        settings_uri = SettingsExtensionSpec.URI

        with subtests.test("agent responds based on enabled thinking setting"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            message.metadata = {
                settings_uri: {
                    "values": {
                        "thinking_group": {
                            "type": "checkbox_group",
                            "values": {"thinking": {"value": True}},
                        }
                    }
                }
            }
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "Thinking mode is enabled" in task.history[-1].parts[0].root.text

        with subtests.test("agent responds based on disabled thinking setting"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            message.metadata = {
                settings_uri: {
                    "values": {
                        "thinking_group": {
                            "type": "checkbox_group",
                            "values": {"thinking": {"value": False}},
                        }
                    }
                }
            }
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "Thinking mode is disabled" in task.history[-1].parts[0].root.text
