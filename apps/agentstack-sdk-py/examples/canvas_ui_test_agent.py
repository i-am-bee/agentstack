# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
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


def generate_recipe_response(recipe_title: str, description: str, closing_message: str) -> str:
    """Generate a recipe response with the given title, description, and closing message."""
    return f"""\
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

{closing_message}
"""


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

    if canvas_edit_request:
        original_recipe = (
            canvas_edit_request.artifact.parts[0].root.text
            if isinstance(canvas_edit_request.artifact.parts[0].root, TextPart)
            else ""
        )
        edited_part = original_recipe[canvas_edit_request.start_index : canvas_edit_request.end_index]

        print("Canvas Edit Request:")
        print(f"Start Index: {canvas_edit_request.start_index}")
        print(f"End Index: {canvas_edit_request.end_index}")
        print(f"Artifact ID: {canvas_edit_request.artifact.artifact_id}")
        print(f"Edited part: {edited_part}")

        description = f"You requested to edit this part:\n\n~~~\n{edited_part}\n~~~\n\n"
        recipe_title = "Canvas Recipe EDITED"
        closing_message = "Enjoy your edited meal!"
    else:
        recipe_title = random.choice(RECIPE_TITLES)
        description = "Here's your recipe:"
        closing_message = "Enjoy your meal!"

    response = generate_recipe_response(recipe_title, description, closing_message)

    match = re.compile(r"```recipe\n(.*?)\n```", re.DOTALL).search(response)

    if not match:
        yield response
        return

    await asyncio.sleep(1)

    if pre_text := response[: match.start()].strip():
        message = AgentMessage(text=pre_text)
        yield message
        await context.store(message)

    await asyncio.sleep(1)

    recipe_content = match.group(1)
    first_line = recipe_content.split("\n", 1)[0]

    # Extract the title and remove it from content if it's a heading
    if first_line.startswith("#"):
        artifact_name = first_line.lstrip("# ").strip()
        # Remove the first line from recipe_content if there's more content
        recipe_content = recipe_content.split("\n", 1)[1].strip() if "\n" in recipe_content else recipe_content
    else:
        artifact_name = "Recipe"

    # Split recipe content into x chunks for streaming
    num_chunks = 8
    content_length = len(recipe_content)
    chunk_size = content_length // num_chunks
    chunks = []

    for i in range(num_chunks):
        start = i * chunk_size
        # Last chunk gets any remaining characters
        end = content_length if i == num_chunks - 1 else (i + 1) * chunk_size
        chunks.append(recipe_content[start:end])

    artifact = AgentArtifact(
        name=artifact_name,
        parts=[TextPart(text=recipe_content)],
    )
    await context.store(artifact)

    # Send first chunk with artifact_id to establish the artifact
    first_artifact = AgentArtifact(
        artifact_id=artifact.artifact_id,
        name=artifact_name,
        parts=[TextPart(text=chunks[0])],
    )
    yield first_artifact

    # Send remaining chunks using the same artifact_id
    for chunk in chunks[1:]:
        chunk_artifact = AgentArtifact(
            artifact_id=artifact.artifact_id,
            name=artifact_name,
            parts=[TextPart(text=chunk)],
        )
        yield chunk_artifact
        await context.store(chunk_artifact)
        await asyncio.sleep(0.3)

    if post_text := response[match.end() :]:
        message = AgentMessage(text=post_text)
        yield message
        await context.store(message)


if __name__ == "__main__":
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
