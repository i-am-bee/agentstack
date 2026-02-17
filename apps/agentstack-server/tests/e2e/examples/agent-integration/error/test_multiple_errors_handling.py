# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions.ui.error import ErrorExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_multiple_errors_handling_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/error/multiple-errors-handling"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent reports multiple errors from ExceptionGroup"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.failed

            # Verify error metadata contains structured error data
            error_uri = ErrorExtensionSpec.URI
            error_metadata = task.status.message.metadata
            assert error_metadata is not None
            assert error_uri in error_metadata

            error_data = error_metadata[error_uri]["error"]
            # ExceptionGroup produces an ErrorGroup with list of errors
            assert "errors" in error_data
            errors = error_data["errors"]
            assert len(errors) == 2

            # Verify both errors are present
            error_titles = {e["title"] for e in errors}
            error_messages = {e["message"] for e in errors}
            assert error_titles == {"ValueError", "TypeError"}
            assert error_messages == {"First error", "Second error"}
