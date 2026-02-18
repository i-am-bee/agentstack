# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


def _task_text(task) -> str:
    return "".join(
        part.root.text
        for message in task.history
        for part in message.parts
        if getattr(part.root, "kind", None) == "text"
    )


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_streaming_buffered_history_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/multi-turn/streaming-buffered-history"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("first turn stores one user message before final buffered assistant write"):
            message = create_text_message_object(content="My first message")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "contains 1 message(s)" in _task_text(task)

        with subtests.test("second turn confirms previous streamed response was stored once"):
            message = create_text_message_object(content="My second message")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "contains 3 message(s)" in _task_text(task)
