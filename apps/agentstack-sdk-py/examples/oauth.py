# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

import pydantic
from a2a.types import Message, Role
from a2a.utils.message import get_message_text
from beeai_framework.adapters.agentstack.backend.chat import AgentStackChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.backend.types import ChatModelParameters
from beeai_framework.tools.mcp import MCPTool
from beeai_framework.tools.think import ThinkTool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client  # pyrefly: ignore [deprecated] -- TODO: upgrade

from agentstack_sdk.a2a.extensions import (
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from agentstack_sdk.a2a.extensions.auth.oauth import (
    OAuthExtensionServer,
    OAuthExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

server = Server()

FrameworkMessage = UserMessage | AssistantMessage


def to_framework_message(message: Message) -> FrameworkMessage:
    """Convert A2A Message to Agent Stack Framework Message format"""
    message_text = "".join(part.root.text for part in message.parts if part.root.kind == "text")

    if message.role == Role.agent:
        return AssistantMessage(message_text)
    elif message.role == Role.user:
        return UserMessage(message_text)
    else:
        raise ValueError(f"Invalid message role: {message.role}")


@server.agent()
async def oauth_agent(
    input: Message,
    context: RunContext,
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
    oauth: Annotated[OAuthExtensionServer, OAuthExtensionSpec.single_demand()],
):
    """Multi-turn chat agent with conversation memory and LLM integration"""
    await context.store(input)

    # pyrefly: ignore [deprecated] -- TODO: upgrade
    mcp_client = streamablehttp_client(
        url="https://mcp.stripe.com",
        auth=await oauth.create_httpx_auth(resource_url=pydantic.AnyUrl("https://mcp.stripe.com")) if oauth else None,
    )

    async with mcp_client as (read, write, _), ClientSession(read, write) as session:
        tools = await MCPTool.from_client(session)

        # Load conversation history
        history = [
            message async for message in context.load_history() if isinstance(message, Message) and message.parts
        ]

        llm_client = AgentStackChatModel(parameters=ChatModelParameters(temperature=0.0))
        llm_client.set_context(llm)

        # Create a RequirementAgent with conversation memory
        agent = RequirementAgent(
            name="Agent",
            llm=llm_client,
            role="helpful assistant",
            instructions="You are a helpful assistant who can integrate with Stripe.",
            tools=[ThinkTool(), *tools],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            save_intermediate_steps=False,
            middlewares=[],
        )

        # Load conversation history into agent memory
        await agent.memory.add_many(to_framework_message(item) for item in history)

        # Process the current message and generate response
        async for event, meta in agent.run(get_message_text(input)):
            if meta.name == "success" and event.state.steps:
                step = event.state.steps[-1]
                if not step.tool:
                    continue

                tool_name = step.tool.name

                if tool_name == "final_answer":
                    response = AgentMessage(text=step.input["response"])

                    yield response
                    await context.store(response)


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        context_store=PlatformContextStore(),  # Enable persistent storage
    )


if __name__ == "__main__":
    run()
