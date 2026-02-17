# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message, TextPart
from agentstack_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from agentstack_sdk.a2a.extensions.ui import CanvasEditRequest
from agentstack_sdk.a2a.extensions.ui.canvas import (
    CanvasExtensionServer,
    CanvasExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentArtifact
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()

BASE_PROMPT = """\
You are a helpful coding assistant.
Generate code enclosed in triple-backtick blocks tagged ```python.
The first line should be a comment with the code's purpose.
"""

EDIT_PROMPT = (
    BASE_PROMPT
    + """
You are editing existing code. The user selected this portion:
```python
{selected_code}
```

They want: {description}

Respond with the FULL updated code. Only change the selected portion.
"""
)


def get_system_prompt(canvas_edit: CanvasEditRequest | None) -> str:
    if not canvas_edit:
        return BASE_PROMPT

    # Check if parts list is not empty and first part is TextPart
    if not canvas_edit.artifact.parts or not isinstance(canvas_edit.artifact.parts[0].root, TextPart):
        return BASE_PROMPT

    original_code = canvas_edit.artifact.parts[0].root.text

    # Validate indices are within bounds
    if not (0 <= canvas_edit.start_index <= canvas_edit.end_index <= len(original_code)):
        return BASE_PROMPT

    selected = original_code[canvas_edit.start_index : canvas_edit.end_index]

    return EDIT_PROMPT.format(selected_code=selected, description=canvas_edit.description)


async def call_llm(llm: LLMServiceExtensionServer, system_prompt: str, message: Message):
    """Call your LLM with the adapted prompt (implementation depends on your LLM framework)."""
    # As a placeholder, we return a mock response.
    example = "```python\n# Hard-coded example (no LLM used). Above is the prompt to use. This is the fake response.\nprint('Hello from LLM!')\n```"
    artifact = AgentArtifact(
        name="Response",
        parts=[
            TextPart(text=system_prompt),  # This is just for demonstration. Replace with actual LLM call.
            TextPart(text=example),  # This is just for demonstration. Replace with actual LLM call.
        ],
    )
    return artifact


@server.agent()
async def canvas_with_llm_example(
    message: Message,
    context: RunContext,
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
    canvas: Annotated[CanvasExtensionServer, CanvasExtensionSpec()],
):
    await context.store(message)
    canvas_edit = await canvas.parse_canvas_edit_request(message=message)

    # Adapt system prompt based on whether this is an edit or new generation
    system_prompt = get_system_prompt(canvas_edit)

    artifact = await call_llm(llm, system_prompt, message)
    yield artifact

    await context.store(artifact)


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
