# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from random import random
from typing import Annotated

import pytest
from a2a.client import Client, ClientEvent
from a2a.client.helpers import create_text_message_object
from a2a.types import Message, Task

from agentstack_sdk.a2a.extensions import (
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from agentstack_sdk.a2a.extensions.services.llm import LLMFulfillment, LLMServiceExtensionClient
from agentstack_sdk.a2a.extensions.ui.error import ErrorMetadata
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

pytestmark = pytest.mark.e2e


async def get_final_task_from_stream(stream: AsyncIterator[ClientEvent | Message]) -> Task:
    final_task = None
    async for event in stream:
        match event:
            case (task, _):
                final_task = task
    return final_task


@pytest.fixture
async def llm_extension_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def chunked_artifact_producer(
        llm_ext: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
    ) -> AsyncGenerator[RunYield, Message]:
        # Agent producing chunked artifacts
        await asyncio.sleep(random() * 0.5)
        api_key = next(iter(llm_ext.data.llm_fulfillments.values())).api_key
        yield api_key

    async with create_server_with_agent(chunked_artifact_producer) as (server, test_client):
        yield server, test_client


async def test_extension_is_not_reused(llm_extension_agent):
    _, client = llm_extension_agent
    card = await client.get_card()
    llm_spec = LLMServiceExtensionSpec.from_agent_card(card)
    extension_client = LLMServiceExtensionClient(llm_spec)

    tasks = []

    for i in range(10):
        message = create_text_message_object()
        message.metadata = extension_client.fulfillment_metadata(
            llm_fulfillments={"default": LLMFulfillment(api_key=str(i), api_model="model", api_base="base")}
        )
        tasks.append(asyncio.create_task(get_final_task_from_stream(client.send_message(message))))

    results = await asyncio.gather(*tasks)
    for i, task in enumerate(results):
        assert task.history[-1].parts[0].root.text == str(i)


@pytest.fixture
async def error_agent_without_stacktrace(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def error_agent(message: Message, context: RunContext) -> AsyncGenerator[RunYield, Message]:
        yield "Processing your request"
        raise ValueError("Something went wrong!")

    async with create_server_with_agent(error_agent) as (server, test_client):
        yield server, test_client


@pytest.fixture
async def exception_group_agent_with_stacktrace(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def exception_group_agent(
        message: Message,
        context: RunContext,
        error_ext: Annotated[ErrorExtensionServer, ErrorExtensionSpec(ErrorExtensionParams(include_stacktrace=True))],
    ) -> AsyncGenerator[RunYield, Message]:
        yield "Processing multiple operations"
        exc1 = ValueError("First error")
        exc2 = TypeError("Second error")
        raise ExceptionGroup("Multiple failures", [exc1, exc2])

    async with create_server_with_agent(exception_group_agent) as (server, test_client):
        yield server, test_client


async def test_error_extension_without_stacktrace(error_agent_without_stacktrace):
    """Test that errors are properly handled without stack trace."""
    _, client = error_agent_without_stacktrace
    card = await client.get_card()
    error_spec = ErrorExtensionSpec.from_agent_card(card)

    message = create_text_message_object()
    task = await get_final_task_from_stream(client.send_message(message))

    # Find the error message in history
    error_message = None
    for msg in task.history:
        if msg.metadata and error_spec.URI in msg.metadata:
            error_message = msg
            break

    assert error_message is not None, "Error message not found in task history"

    # Validate error metadata
    error_metadata = ErrorMetadata.model_validate(error_message.metadata[error_spec.URI])
    assert error_metadata.error.title == "ValueError"
    assert error_metadata.error.message == "Something went wrong!"
    assert error_metadata.stack_trace is None

    # Check message text
    message_text = error_message.parts[0].root.text
    assert "## ValueError" in message_text
    assert "Something went wrong!" in message_text
    assert "```" not in message_text  # No stack trace code block


async def test_error_extension_exception_group_with_stacktrace(exception_group_agent_with_stacktrace):
    """Test that exception groups include single stack trace when configured."""
    _, client = exception_group_agent_with_stacktrace
    card = await client.get_card()
    error_spec = ErrorExtensionSpec.from_agent_card(card)

    message = create_text_message_object()
    task = await get_final_task_from_stream(client.send_message(message))

    # Find the error message
    error_message = None
    for msg in task.history:
        if msg.metadata and error_spec.URI in msg.metadata:
            error_message = msg
            break

    assert error_message is not None

    # Validate error metadata - should have 2 errors in the group
    error_metadata = ErrorMetadata.model_validate(error_message.metadata[error_spec.URI])
    assert error_metadata.error.message.startswith("Multiple failures")
    assert len(error_metadata.error.errors) == 2
    assert error_metadata.error.errors[0].title == "ValueError"
    assert error_metadata.error.errors[0].message == "First error"
    assert error_metadata.error.errors[1].title == "TypeError"
    assert error_metadata.error.errors[1].message == "Second error"

    # Should have a single stack trace for the entire group
    assert error_metadata.stack_trace is not None
    assert "ExceptionGroup: Multiple failures" in error_metadata.stack_trace
    assert "ValueError: First error" in error_metadata.stack_trace
    assert "TypeError: Second error" in error_metadata.stack_trace

    # Check message text
    message_text = error_message.parts[0].root.text
    assert "## Multiple failures" in message_text
    assert "### ValueError" in message_text
    assert "First error" in message_text
    assert "### TypeError" in message_text
    assert "Second error" in message_text
    assert "## Stack Trace" in message_text
    assert "```" in message_text
    assert "ExceptionGroup" in message_text


@pytest.fixture
async def context_isolation_agent(create_server_with_agent) -> AsyncGenerator[tuple[Server, Client]]:
    async def error_agent(
        message: Message,
        context: RunContext,
        error_ext: Annotated[ErrorExtensionServer, ErrorExtensionSpec(ErrorExtensionParams())],
    ) -> AsyncGenerator[RunYield, Message]:
        # Extract request_id from message text to set unique context
        text_content = ""
        for part in message.parts:
            if hasattr(part.root, "text"):
                text_content = part.root.text
                break

        # Set context based on the request
        error_ext.context["request_id"] = text_content
        error_ext.context["timestamp"] = text_content  # Use text as unique identifier

        # Simulate some async work
        await asyncio.sleep(0.1)

        yield f"Processing request: {text_content}"
        raise ValueError(f"Error for request {text_content}")

    async with create_server_with_agent(error_agent) as (server, test_client):
        yield server, test_client


async def test_error_extension_context_isolation(context_isolation_agent):
    """Test that error context is isolated between parallel requests."""
    _, client = context_isolation_agent
    card = await client.get_card()
    error_spec = ErrorExtensionSpec.from_agent_card(card)

    # Send 3 parallel requests with different identifiers
    request_ids = ["request-1", "request-2", "request-3"]

    # Create tasks for parallel execution
    async def send_request(request_id: str) -> Task:
        message = create_text_message_object(content=request_id)
        return await get_final_task_from_stream(client.send_message(message))

    # Execute all requests in parallel
    tasks = await asyncio.gather(*[send_request(rid) for rid in request_ids])

    # Validate each task has the correct context
    for task, expected_id in zip(tasks, request_ids, strict=True):
        # Find the error message
        error_message = None
        for msg in task.history:
            if msg.metadata and error_spec.URI in msg.metadata:
                error_message = msg
                break

        assert error_message is not None, f"Error message not found for {expected_id}"

        # Validate error metadata
        error_metadata = ErrorMetadata.model_validate(error_message.metadata[error_spec.URI])
        assert error_metadata.error.title == "ValueError"
        assert error_metadata.error.message == f"Error for request {expected_id}"

        # Validate context isolation - each request should have its own context
        assert error_metadata.context is not None, f"Context missing for {expected_id}"
        assert error_metadata.context["request_id"] == expected_id, (
            f"Expected request_id '{expected_id}', got '{error_metadata.context['request_id']}'"
        )
        assert error_metadata.context["timestamp"] == expected_id, (
            f"Expected timestamp '{expected_id}', got '{error_metadata.context['timestamp']}'"
        )
