# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


def _history_text(task) -> str:
    """Concatenate all text parts from stored history items.

    The streaming-agent-history agent stores one aggregated message per turn,
    so all buffered partial outputs are present as a single joined entry in history.
    """
    return "".join(
        part.root.text
        for message in task.history
        for part in message.parts
        if getattr(part.root, "kind", None) == "text"
    )


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_streaming_buffered_history_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/multi-turn/streaming-agent-history"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("first turn history summary shows total=1 and user=1"):
            message = create_text_message_object(content="My first message")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            text = _history_text(task)
            assert "total=1" in text and "user=1" in text
            assert "Error during execution" not in text

        with subtests.test("second turn history summary shows total=3 and user=2"):
            message = create_text_message_object(content="My second message")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            text = _history_text(task)
            assert "total=3" in text and "user=2" in text
            assert "Error during execution" not in text

        with subtests.test("third turn exceeds history limit and stores exception message instead"):
            message = create_text_message_object(content="My third message")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            text = _history_text(task)
            # The tool call completes successfully before the error occurs, so we expect to see the tool result part followed by the error message about history being too long.
            assert "Tool call completed with result:" in text
            assert "Error during execution: History is too long!" in text
            assert "History message counts" not in text
