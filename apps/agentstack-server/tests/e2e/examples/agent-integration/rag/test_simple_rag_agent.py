# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from contextlib import suppress
from pathlib import Path
from uuid import uuid4

import pytest
from a2a.types import Message, Part, Role, TaskState, TextPart
from agentstack_sdk.a2a.extensions import (
    EmbeddingFulfillment,
    EmbeddingServiceExtensionClient,
    EmbeddingServiceExtensionSpec,
)
from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionClient, PlatformApiExtensionSpec
from agentstack_sdk.platform import File, ModelProvider, SystemConfiguration
from agentstack_sdk.platform.context import ContextPermissions, Permissions

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e

EMBEDDING_MODEL = "other:nomic-embed-text:latest"
FIXTURE_DIR = Path(__file__).parent


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_simple_rag_agent_example(subtests, get_final_task_from_stream, a2a_client_factory, test_configuration):
    # Set up model provider for embeddings (same as setup_real_llm but inline)
    with suppress(Exception):
        await ModelProvider.create(
            name="test_config",
            type=test_configuration.llm_provider_type,
            base_url=test_configuration.llm_api_base.get_secret_value(),
            api_key=test_configuration.llm_api_key.get_secret_value(),
        )
    await SystemConfiguration.update(default_embedding_model=EMBEDDING_MODEL)

    example_path = "agent-integration/rag/simple-rag-agent"

    async with run_example(example_path, a2a_client_factory) as running_example:
        with subtests.test("agent processes file and returns search results"):
            # Upload a test file with multiple distinct sections for meaningful search
            file_content = (FIXTURE_DIR / "zorblax_spec.md").read_bytes()
            file = await File.create(
                filename="zorblax_spec.md",
                content=file_content,
                content_type="text/markdown",
                context_id=running_example.context.id,
            )

            # Generate token with permissions for embeddings, files, and vector stores
            token = await running_example.context.generate_token(
                grant_context_permissions=ContextPermissions(
                    files={"read", "write", "extract"},
                    vector_stores={"read", "write"},
                ),
                grant_global_permissions=Permissions(embeddings={"*"}, a2a_proxy={"*"}),
            )

            # Prepare embedding extension metadata
            embedding_spec = EmbeddingServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)
            embedding_metadata = EmbeddingServiceExtensionClient(embedding_spec).fulfillment_metadata(
                embedding_fulfillments={
                    "default": EmbeddingFulfillment(
                        api_key=token.token.get_secret_value(),
                        api_model=EMBEDDING_MODEL,
                        api_base="{platform_url}/api/v1/openai/",
                    )
                }
            )

            # Prepare platform API auth metadata
            platform_api_client = PlatformApiExtensionClient(PlatformApiExtensionSpec())
            platform_metadata = platform_api_client.api_auth_metadata(
                auth_token=token.token,
                expires_at=token.expires_at,
            )

            # Create message with file and query
            message = Message(
                role=Role.user,
                parts=[
                    Part(root=file.to_file_part()),
                    Part(root=TextPart(text="How much power does the Zorblax engine need?")),
                ],
                context_id=running_example.context.id,
                message_id=str(uuid4()),
                metadata=embedding_metadata | platform_metadata,
            )

            # Send message
            task = await get_final_task_from_stream(running_example.client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"

            # Verify results contain the relevant chunk (Power Requirements)
            result_text = task.history[-1].parts[0].root.text
            assert "Results" in result_text
            assert "42 gigawatts" in result_text
