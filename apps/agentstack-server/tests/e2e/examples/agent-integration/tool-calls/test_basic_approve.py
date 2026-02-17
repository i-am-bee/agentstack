# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, Role, TaskState
from agentstack_sdk.a2a.extensions import ApprovalExtensionClient, ApprovalExtensionSpec
from agentstack_sdk.a2a.extensions.interactions.approval import ApprovalResponse

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_basic_approve_example(subtests, a2a_client_factory, test_configuration):
    example_path = "agent-integration/tool-calls/basic-approve"

    async with run_example(
        example_path,
        a2a_client_factory,
        llm_model=test_configuration.llm_model,
        llm_api_key=test_configuration.llm_api_key,
    ) as running_example:
        spec = ApprovalExtensionSpec.from_agent_card(running_example.provider.agent_card)
        approval_client = ApprovalExtensionClient(spec)

        with subtests.test("tool call is approved"):
            # Send message that should trigger the ThinkTool
            message = create_text_message_object(content="Think deeply about the meaning of life")
            message.context_id = running_example.context.id
            message.metadata = approval_client.metadata()

            # Get initial task - may go to input_required if tool is called
            task = None
            async for event in running_example.client.send_message(message):
                if isinstance(event, tuple):
                    task, _ = event

            # If tool call needs approval, approve it
            while task and task.status.state == TaskState.input_required:
                response = ApprovalResponse(decision="approve")
                response_message = Message(
                    role=Role.user,
                    message_id=str(uuid4()),
                    task_id=task.id,
                    context_id=running_example.context.id,
                    parts=[],
                    metadata={spec.URI: response.model_dump(mode="json")},
                )
                async for event in running_example.client.send_message(response_message):
                    if isinstance(event, tuple):
                        task, _ = event

            assert task is not None
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

        with subtests.test("tool call is rejected"):
            # Send message that should trigger the ThinkTool
            message = create_text_message_object(content="Think about what makes humans unique")
            message.context_id = running_example.context.id
            message.metadata = approval_client.metadata()

            # Get initial task
            task = None
            async for event in running_example.client.send_message(message):
                if isinstance(event, tuple):
                    task, _ = event

            # If tool call needs approval, reject it
            if task and task.status.state == TaskState.input_required:
                response = ApprovalResponse(decision="reject")
                response_message = Message(
                    role=Role.user,
                    message_id=str(uuid4()),
                    task_id=task.id,
                    context_id=running_example.context.id,
                    parts=[],
                    metadata={spec.URI: response.model_dump(mode="json")},
                )
                async for event in running_example.client.send_message(response_message):
                    if isinstance(event, tuple):
                        task, _ = event

            assert task is not None
            # Task may fail or complete depending on how agent handles rejection
            assert task.status.state in (TaskState.completed, TaskState.failed)
