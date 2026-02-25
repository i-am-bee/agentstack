# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from textwrap import dedent
from threading import Thread
from typing import Any
from unittest import mock

import kr8s
import pytest
import uvicorn
from a2a.client import A2AClientHTTPError
from a2a.client.helpers import create_text_message_object
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCapabilities, AgentCard, Role, Task, TaskState
from agentstack_sdk.a2a.extensions import LLMFulfillment, LLMServiceExtensionClient, LLMServiceExtensionSpec
from agentstack_sdk.platform import ModelProvider, Provider
from agentstack_sdk.platform.context import Context, ContextPermissions, Permissions
from kr8s.asyncio.objects import Deployment

pytestmark = pytest.mark.e2e


def extract_agent_text_from_stream(task: Task) -> str:
    assert task.history
    return "".join(item.parts[0].root.text for item in task.history if item.role == Role.agent if item.parts)


@pytest.mark.usefixtures("clean_up", "setup_real_llm", "setup_platform_client")
async def test_imported_agent(
    subtests, a2a_client_factory, get_final_task_from_stream, test_configuration, kr8s_client: kr8s.Api
):
    agent_image = test_configuration.test_agent_image
    with subtests.test("add chat agent"):
        _ = await Provider.create(location=agent_image)
        providers = await Provider.list()
        context = await Context.create()
        context_token = await context.generate_token(
            providers=providers,
            grant_global_permissions=Permissions(llm={"*"}),
            grant_context_permissions=ContextPermissions(context_data={"*"}),
        )
        assert len(providers) == 1
        assert providers[0].source == agent_image
        assert providers[0].agent_card

    async with a2a_client_factory(providers[0].agent_card, context_token) as a2a_client:
        with subtests.test("run chat agent for the first time"):
            num_parallel = 3
            message = create_text_message_object(
                content=(
                    "How do you say informal hello in italian in 4 letters? "
                    "DO NOT SEARCH THE INTERNET FOR THIS, ANSWER DIRECTLY FROM YOUR KNOWLEDGE. "
                    "ANSWER ONLY THOSE FOUR LETTERS."
                )
            )
            spec = LLMServiceExtensionSpec.from_agent_card(providers[0].agent_card)
            message.metadata = LLMServiceExtensionClient(spec).fulfillment_metadata(
                llm_fulfillments={
                    "default": LLMFulfillment(
                        api_key=context_token.token.get_secret_value(),
                        api_model=(await ModelProvider.match())[0].model_id,
                        api_base="{platform_url}/api/v1/openai/",
                    )
                }
            )
            message.context_id = context.id
            task = await get_final_task_from_stream(a2a_client.send_message(message))

            # Verify response
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "ciao" in extract_agent_text_from_stream(task).lower()

            # Run 3 requests in parallel (test that each request waits)
            run_results = await asyncio.gather(
                *(get_final_task_from_stream(a2a_client.send_message(message)) for _ in range(num_parallel))
            )

            for task in run_results:
                assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
                assert "ciao" in extract_agent_text_from_stream(task).lower()

        with subtests.test("run chat agent for the second time"):
            task = await get_final_task_from_stream(a2a_client.send_message(message))
            assert task.status.state == TaskState.completed, f"Fail: {task.status.message.parts[0].root.text}"
            assert "ciao" in extract_agent_text_from_stream(task).lower()

    with subtests.test("the context token will not work with direct call to agent (server exchange is required)"):
        deployment = await Deployment.get("agentstack-server", api=kr8s_client)
        script = dedent(
            f"""\
            import asyncio
            import sys
            import httpx

            async def main():
                url = "http://agentstack-provider-{providers[0].id}-svc:8000/jsonrpc/"
                print(f"Connecting to {{url}}...")
                try:
                    async with httpx.AsyncClient(timeout=None, headers={{"Authorization": "Bearer {context_token.token.get_secret_value()}"}}) as httpx_client:
                        response = await httpx_client.post(url, json={{
                                "jsonrpc": "2.0",
                                "id": "1",
                                "method": "message/send",
                                "params": {{
                                    "message": {{
                                        "role": "agent",
                                        "parts": [{{"kind": "text", "text": "Hello"}}],
                                        "messageId": "1",
                                        "kind": "message",
                                    }}
                                }}
                            }})
                        response.raise_for_status()
                except Exception as e:
                    if "401" in str(e):
                        print("Success: Request failed as expected with 401")
                        sys.exit(0)
                    print(f"Error: {{e}}")
                    sys.exit(1)

                print("Error: Request succeeded unexpectedly")
                sys.exit(1)

            asyncio.run(main())
            """
        )
        resp = await deployment.exec(["python", "-c", script], check=False)
        assert resp.returncode == 0, resp.stdout.decode("utf-8") + "\n" + resp.stderr.decode("utf-8")

    invalid_context_token = await context.generate_token(
        providers=[str(uuid.uuid4())],  # different target provider
        grant_global_permissions=Permissions(llm={"*"}),
        grant_context_permissions=ContextPermissions(context_data={"*"}),
    )
    async with a2a_client_factory(providers[0].agent_card, invalid_context_token) as a2a_client:
        with (
            subtests.test("run chat agent with invalid token"),
            pytest.raises(A2AClientHTTPError, match="403 Forbidden"),
        ):
            await get_final_task_from_stream(a2a_client.send_message(message))


UNMANAGED_AGENT_CARD: dict[str, Any] = {
    "authentication": {"schemes": ["Bearer"]},
    "capabilities": AgentCapabilities(streaming=True),
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "description": "Test unmanaged A2A agent",
    "name": "UnmanagedTestAgent",
    "skills": [{"id": "skill-1", "name": "Echo", "description": "Echoes back", "tags": ["test"]}],
    "url": "http://example.com/agent",
    "version": "1.0",
}


@pytest.fixture
def unmanaged_a2a_server(free_port, setup_platform_client, clean_up_fn):
    server_instance: uvicorn.Server | None = None
    thread: Thread | None = None

    agent_card = AgentCard(**UNMANAGED_AGENT_CARD)
    agent_card.url = f"http://host.docker.internal:{free_port}"

    handler = mock.AsyncMock()

    def start_server():
        nonlocal server_instance, thread

        app = A2AStarletteApplication(agent_card, handler)
        config = uvicorn.Config(app=app.build(), port=free_port, log_level="warning")
        server_instance = uvicorn.Server(config)

        def run_server():
            with contextlib.suppress(KeyboardInterrupt):
                server_instance.run()

        thread = Thread(target=run_server, name="unmanaged-a2a-server")
        thread.start()
        while not server_instance.started:
            time.sleep(0.1)

    try:
        yield free_port, start_server
    finally:
        asyncio.run(clean_up_fn())
        if server_instance:
            server_instance.should_exit = True
        if thread:
            thread.join(timeout=5)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_unmanaged_a2a_agent(unmanaged_a2a_server):
    port, start_server = unmanaged_a2a_server
    start_server()

    provider = await Provider.create(location=f"http://host.docker.internal:{port}")

    assert provider.managed is False
    assert provider.agent_card is not None
    assert provider.agent_card.name == "UnmanagedTestAgent"
    assert provider.agent_card.description == "Test unmanaged A2A agent"
    assert provider.agent_card.skills is not None
    assert len(provider.agent_card.skills) == 1

    assert len(provider.agent_card.capabilities.extensions) == 1
    assert (
        provider.agent_card.capabilities.extensions[0].uri
        == "https://a2a-extensions.agentstack.beeai.dev/ui/agent-detail/v1"
    )
