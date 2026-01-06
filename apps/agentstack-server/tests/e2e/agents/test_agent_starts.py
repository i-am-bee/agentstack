# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid
from textwrap import dedent

import kr8s
import pytest
from a2a.client import A2AClientHTTPError
from a2a.client.helpers import create_text_message_object
from a2a.types import Role, Task, TaskState
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
