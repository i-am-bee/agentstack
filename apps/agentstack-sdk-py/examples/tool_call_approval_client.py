# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid

import a2a.client
import a2a.types
import httpx

import agentstack_sdk.a2a.extensions
from agentstack_sdk.a2a.extensions.tools.call import ToolCallResponse


async def run(base_url: str = "http://127.0.0.1:10000"):
    async with httpx.AsyncClient(timeout=30) as httpx_client:
        card = await a2a.client.A2ACardResolver(httpx_client, base_url=base_url).get_agent_card()
        tool_call_spec = agentstack_sdk.a2a.extensions.ToolCallExtensionSpec.from_agent_card(card)

        if not tool_call_spec:
            raise ValueError(f"Agent at {base_url} does not support MCP Tool Call extension")

        tool_call_extension_client = agentstack_sdk.a2a.extensions.ToolCallExtensionClient(tool_call_spec)

        message = a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[a2a.types.Part(root=a2a.types.TextPart(text="Howdy!"))],
            metadata=tool_call_extension_client.metadata(),
        )

        client = a2a.client.ClientFactory(a2a.client.ClientConfig(httpx_client=httpx_client, polling=True)).create(
            card=card
        )

        task = None
        while True:
            async for event in client.send_message(message):
                if isinstance(event, a2a.types.Message):
                    print(event)
                    return
                task, _update = event

            if task and task.status.state == a2a.types.TaskState.input_required:
                if not task.status.message:
                    raise RuntimeError("Missing message")

                approval_request = tool_call_extension_client.parse_request(message=task.status.message)

                print("Agent has requested a tool call")
                print(approval_request)
                choice = input("Approve (Y/n): ")
                response = ToolCallResponse(action="accept" if choice.lower() == "y" else "reject")
                message = tool_call_extension_client.create_response_message(task_id=task.id, response=response)
            else:
                break

        print(task)


if __name__ == "__main__":
    asyncio.run(run())
