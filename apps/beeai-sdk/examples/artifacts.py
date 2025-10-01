# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import re
from typing import Annotated

from a2a.types import Message, Role, TextPart
from a2a.utils.message import get_message_text
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.tools.think import ThinkTool

from beeai_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from beeai_sdk.a2a.extensions.ui.canvas import CanvasEditRequest, CanvasExtensionServer, CanvasExtensionSpec
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


BASE_PROMPT = """\
You are a helpful assistant that creates cooking recipes.

- The recipe should be formatted as markdown and be enclosed in a triple-backtick code block tagged ```recipe.
- The first line after that should be the recipe name as a top-level heading.

Example:

```recipe
# Bread with butter

## Ingredients
- bread (1 slice)
- butter (1 slice)

## Instructions
1. Cut a slice of bread.
2. Cut a slice of butter.
3. Spread the slice of butter on the slice of bread.
"""

EDIT_PROMPT = (
    BASE_PROMPT
    + """
You are given previous recipe and the changes that the user has made to the recipe. You should use the changes to help the user draft a new recipe.

Here is the previous recipe:
```recipe
{artifact_text}
```

Here is the part of the recipe that user wishes to change:
```recipe-edit-part
{artifact_text_substring}
```

The requested change is:
```recipe-edit-description
{edit_description}
```

Respond with the recipe in full, with the given part changed according to the request. IMPORTANT NOTE: Do not change ANYTHING outside of the part of the recipe that user wishes to change.
"""
)


def get_system_prompt(canvas_edit_request: CanvasEditRequest | None) -> str:
    if not canvas_edit_request:
        return BASE_PROMPT
    original_recipe = (
        canvas_edit_request.artifact.parts[0].root.text
        if isinstance(canvas_edit_request.artifact.parts[0].root, TextPart)
        else ""
    )
    return EDIT_PROMPT.format(
        artifact_text=original_recipe,
        artifact_text_substring=original_recipe[canvas_edit_request.start_index : canvas_edit_request.end_index],
        edit_description=canvas_edit_request.description,
    )


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
):
    """Works with artifacts"""

    canvas_edit_request = await canvas.parse_canvas_edit_request(message=input)

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

    history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]

    agent = RequirementAgent(
        llm=llm_client,
        role="helpful assistant",
        instructions=get_system_prompt(canvas_edit_request),
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
                match = re.compile(r"```recipe\n(.*?)\n```", re.DOTALL).search(response)

                if not match:
                    yield response
                    continue

                if pre_text := response[: match.start()].strip():
                    yield pre_text

                recipe_content = match.group(1).strip()
                first_line = recipe_content.split("\n", 1)[0]
                yield AgentArtifact(
                    name=first_line.lstrip("# ").strip() if first_line.startswith("#") else "Recipe",
                    parts=[TextPart(text=recipe_content)],
                )

                if post_text := response[match.end() :].strip():
                    yield post_text


if __name__ == "__main__":
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
