# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions.ui.error import ErrorExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_adding_error_context_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/error/adding-error-context"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent includes context in error metadata"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.failed

            # Verify error metadata contains context
            error_uri = ErrorExtensionSpec.URI
            error_metadata = task.status.message.metadata
            assert error_metadata is not None
            assert error_uri in error_metadata

            error_data = error_metadata[error_uri]

            # Verify context is included
            assert error_data["context"] is not None
            assert error_data["context"]["request_id"] == "req-123"
            assert error_data["context"]["user_id"] == 42

            # Verify error details
            assert error_data["error"]["title"] == "ValueError"
            assert error_data["error"]["message"] == "Something went wrong!"
