# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import uuid4

import pytest
from a2a.types import Message, Role, TaskState
from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionClient, PlatformApiExtensionSpec
from agentstack_sdk.platform import File
from agentstack_sdk.platform.context import ContextPermissions, Permissions
from agentstack_sdk.util.file import load_file

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_file_processing_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/files/file-processing"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent processes uploaded file and returns it"):
            # upload test file
            file = await File.create(
                filename="f.txt",
                content=b"0123456789",
                content_type="text/plain",
                context_id=running_example.context.id,
            )

            # create message with auth credentials
            api_extension_client = PlatformApiExtensionClient(PlatformApiExtensionSpec())

            # create a token with file read and write permissions for the agent to be able to read the uploaded file and upload the processed file
            token = await running_example.context.generate_token(
                grant_context_permissions=ContextPermissions(files={"read", "write"}),
                grant_global_permissions=Permissions(a2a_proxy={"*"}),
            )

            message = Message(
                role=Role.user,
                parts=[file.to_file_part()],
                context_id=running_example.context.id,
                message_id=str(uuid4()),
                metadata=api_extension_client.api_auth_metadata(auth_token=token.token, expires_at=token.expires_at),
            )

            # send message
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            # verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

            # check that first message is the content of the first_file

            async with load_file(task.history[-2].parts[0].root) as processed_file:
                assert processed_file.text == "0123456789"

            first_message_text = task.history[-1].parts[0].root.text
            assert first_message_text == "File processing complete"
