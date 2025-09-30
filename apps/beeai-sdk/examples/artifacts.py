# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message, Role, TaskStatus, TextPart
from a2a.utils.message import get_message_text
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.tools.think import ThinkTool

from beeai_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from beeai_sdk.a2a.extensions.ui.canvas import ArtifactChangeResponse, CanvasExtensionServer, CanvasExtensionSpec
from beeai_sdk.a2a.types import AgentArtifact
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext

server = Server()


FrameworkMessage = UserMessage | AssistantMessage


def to_framework_message(message: Message) -> FrameworkMessage:
    """Convert A2A Message to BeeAI Framework Message format"""
    message_text = "".join(part.root.text for part in message.parts if part.root.kind == "text")

    if message.role == Role.agent:
        return AssistantMessage(message_text)
    elif message.role == Role.user:
        return UserMessage(message_text)
    else:
        raise ValueError(f"Invalid message role: {message.role}")


def def_get_system_prompt(canvas_data: ArtifactChangeResponse | None) -> str:
    base_prompt = "You are a helpful assistant that should help user draft a cooking recipe. Producing a recipe should always be in the markdown format and should always be started with a header with # Cooking Recipe: NAME OF THE RECIPE."
    if canvas_data:
        original_recipe = canvas_data.artifact.parts[0].root.text
        return f"""
    {base_prompt}
    You are given previous recipe and the changes that the user has made to the recipe. You should use the changes to help the user draft a new recipe.

    Here is the previous recipe:
        {original_recipe}

    Here is the part of the recipe that user wishes to change:
        {original_recipe[canvas_data.start_index : canvas_data.end_index]}

    IMPORTANT NOTE: Do not change ANYTHING outside of the part of the recipe that user wishes to change.
    """
    else:
        return base_prompt


@server.agent()
async def artifacts_agent(
    input: Message,
    context: RunContext,
    llm: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(),
    ],
    canvas: Annotated[
        CanvasExtensionServer,
        CanvasExtensionSpec(),
    ],
) -> AsyncGenerator[TaskStatus | Message | str, Message]:
    """Works with artifacts"""

    canvas_data = await canvas.parse_canvas_response(message=input)

    if not llm or not llm.data:
        raise ValueError("LLM service extension is required but not available")

    llm_config = llm.data.llm_fulfillments.get("default")

    if not llm_config:
        raise ValueError("LLM service extension provided but no fulfillment available")

    llm_client = OpenAIChatModel(
        model_id=llm_config.api_model,
        base_url=llm_config.api_base,
        api_key=llm_config.api_key,
        tool_choice_support=set(),
    )

    history = [
        message async for message in context.store.load_history() if isinstance(message, Message) and message.parts
    ]

    agent = RequirementAgent(
        llm=llm_client,
        role="helpful assistant",
        instructions=def_get_system_prompt(canvas_data),
        tools=[ThinkTool()],
        requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
        save_intermediate_steps=False,
        middlewares=[],
    )

    await agent.memory.add_many(to_framework_message(item) for item in history)

    async for event, meta in agent.run(get_message_text(input)):
        if meta.name == "success" and event.state.steps:
            step = event.state.steps[-1]
            if not step.tool:
                continue

            tool_name = step.tool.name

            if tool_name == "final_answer":
                response = step.input["response"]

                if response.startswith("# Cooking Recipe:"):
                    lines = response.split("\n")
                    header_line = lines[0]
                    recipe_name = header_line.replace("# Cooking Recipe:", "").strip()

                    yield AgentArtifact(name=recipe_name, parts=[TextPart(text=response)])
                else:
                    yield response


if __name__ == "__main__":
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
