# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import random
import re
from typing import Annotated

from a2a.types import Message, TextPart

from agentstack_sdk.a2a.extensions.ui.canvas import CanvasExtensionServer, CanvasExtensionSpec
from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()

RECIPE_TITLES = [
    "Bread with butter",
    "Classic Spaghetti Carbonara",
    "Chocolate Chip Cookies",
    "Caesar Salad",
    "Grilled Cheese Sandwich",
    "Banana Smoothie",
    "Margherita Pizza",
    "Chicken Stir-Fry",
    "French Toast",
    "Avocado Toast",
]


@server.agent(
    name="Canvas example agent",
)
async def artifacts_agent(
    input: Message,
    context: RunContext,
    canvas: Annotated[
        CanvasExtensionServer,
        CanvasExtensionSpec(),
    ],
):
    """Works with artifacts"""

    await context.store(input)

    canvas_edit_request = await canvas.parse_canvas_edit_request(message=input)

    print(f"Canvas Edit Request: {canvas_edit_request}")

    if canvas_edit_request:
        recipe_title = "Canvas Recipe EDITED"

        original_recipe = (
            canvas_edit_request.artifact.parts[0].root.text
            if isinstance(canvas_edit_request.artifact.parts[0].root, TextPart)
            else ""
        )
        edited_part = original_recipe[canvas_edit_request.start_index : canvas_edit_request.end_index]
        description = f"You requested to edit this part:\n\n*{edited_part}*\n\n"

        response = f"""\
{description}

```recipe
# Canvas Recipe EDITED

## Ingredients
- bread (1 slice)
- butter (1 slice)

## Instructions
1. Cut a slice of bread.
2. Cut a slice of butter.
3. Spread the slice of butter on the slice of bread.
```

Enjoy your edited meal!
"""
    else:
        recipe_title = random.choice(RECIPE_TITLES)
        description = "Here's your recipe:"

        response = f"""\
{description}

```recipe
# {recipe_title}

## Ingredients
- bread (1 slice)
- butter (1 slice)

## Instructions
1. Cut a slice of bread.
2. Cut a slice of butter.
3. Spread the slice of butter on the slice of bread.
```

Enjoy your meal!
"""

    match = re.compile(r"```recipe\n(.*?)\n```", re.DOTALL).search(response)
    print(
        f"Match: {match}\npre_text: {response[: match.start() if match else 'N/A']}\npost_text: {response[match.end() if match else 'N/A' :]}"
    )

    if not match:
        yield response
        return

    if pre_text := response[: match.start()].strip():
        message = AgentMessage(text=pre_text)
        yield message
        await context.store(message)

    recipe_content = match.group(1).strip()
    first_line = recipe_content.split("\n", 1)[0]
    artifact = AgentArtifact(
        # artifact_id='recipe-artifact-1',
        name=first_line.lstrip("# ").strip() if first_line.startswith("#") else "Recipe",
        parts=[TextPart(text=recipe_content)],
    )
    yield artifact
    await context.store(artifact)

    if post_text := response[match.end() :].strip():
        message = AgentMessage(text=post_text)
        yield message
        await context.store(message)


if __name__ == "__main__":
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
