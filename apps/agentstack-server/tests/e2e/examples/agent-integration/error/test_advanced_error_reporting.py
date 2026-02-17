# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions.ui.error import ErrorExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_advanced_error_reporting_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/error/advanced-error-reporting"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent reports error with stack trace"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.failed

            # Verify error message content
            error_text = task.status.message.parts[0].root.text
            assert "ValueError" in error_text
            assert "Something went wrong!" in error_text
            assert "Stack Trace" in error_text

            # Verify error metadata includes stack trace
            error_uri = ErrorExtensionSpec.URI
            error_metadata = task.status.message.metadata
            assert error_metadata is not None
            assert error_uri in error_metadata
            assert error_metadata[error_uri]["stack_trace"] is not None
