# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_basic_environment_variables_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/env-variables/basic-environment-variables"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent responds based on default env variable value"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            # THINKING_ENABLED defaults to false when not set
            assert "Thinking mode is disabled" in task.history[-1].parts[0].root.text
