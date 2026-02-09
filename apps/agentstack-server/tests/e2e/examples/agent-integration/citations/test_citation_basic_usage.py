# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions import CitationExtensionSpec

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_citation_basic_usage_example(subtests, get_final_task_from_stream, a2a_client_factory):
    example_path = "agent-integration/citations/citation-basic-usage"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent responds with text and citation metadata"):
            message = create_text_message_object(content="Hello")
            message.context_id = running_example.context.id
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

            # Verify response text
            response_text = task.history[-1].parts[0].root.text
            assert "Python is the most popular programming language" in response_text

            # Verify citation metadata exists
            citation_uri = CitationExtensionSpec.URI
            response_metadata = task.history[-1].metadata
            assert response_metadata is not None
            assert citation_uri in response_metadata

            # Verify citation content
            citations = response_metadata[citation_uri]["citations"]
            assert len(citations) == 1
            assert citations[0]["url"] == "https://survey.stackoverflow.com/2023"
            assert citations[0]["title"] == "Stack Overflow Developer Survey 2023"
