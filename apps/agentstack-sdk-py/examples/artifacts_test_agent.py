# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import re
from typing import Annotated

from a2a.types import Message, TextPart

from agentstack_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from agentstack_sdk.a2a.extensions.ui.canvas import CanvasExtensionServer, CanvasExtensionSpec
from agentstack_sdk.a2a.types import AgentArtifact
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent(
    name="Canvas example agent",
)
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

    # canvas_edit_request = await canvas.parse_canvas_edit_request(message=input)

    # history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]

    response = """\
Here's your recipe:

```recipe
# Bread with butter

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
