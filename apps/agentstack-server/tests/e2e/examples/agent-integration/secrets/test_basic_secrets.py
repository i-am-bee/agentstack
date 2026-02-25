# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import uuid4

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, Role, TaskState
from agentstack_sdk.a2a.extensions.auth.secrets import SecretsExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_basic_secrets_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/secrets/basic-secrets"

    async with run_example(example_path, a2a_client_factory) as running_example:
        secrets_uri = SecretsExtensionSpec.URI

        with subtests.test("agent uses provided secret"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            message.metadata = {
                secrets_uri: {"secret_fulfillments": {"SLACK_API_KEY": {"secret": "test-slack-api-key-12345"}}}
            }
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "Slack API key: test-slack-api-key-12345" in task.history[-1].parts[0].root.text

        with subtests.test("agent handles missing secret"):
            # Send message without secret - agent will request it
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.auth_required

            # Respond without providing the secret
            response_message = Message(
                role=Role.user,
                message_id=str(uuid4()),
                task_id=task.id,
                context_id=running_example.context.id,
                parts=[],
            )
            final_task = await get_final_task_from_stream(running_example.client.send_message(response_message))

            assert final_task.status.state == TaskState.completed, (
                f"Fail: {final_task.status.message.parts[0].root.text}"
            )
            assert "No Slack API key provided" in final_task.history[-1].parts[0].root.text
