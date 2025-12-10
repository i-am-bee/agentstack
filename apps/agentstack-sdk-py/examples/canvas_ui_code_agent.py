# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import random
import re
from typing import Annotated

from a2a.types import Message, TextPart

from agentstack_sdk.a2a.extensions import (
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
)
from agentstack_sdk.a2a.extensions.ui.canvas import CanvasExtensionServer, CanvasExtensionSpec
from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()

CODE_TITLES = [
    "Fibonacci Generator",
    "Prime Number Checker",
    "Binary Search Implementation",
    "String Reverser",
    "Palindrome Checker",
    "Temperature Converter",
    "Factorial Calculator",
    "List Sorter",
    "FizzBuzz Solution",
    "Word Counter",
]


def generate_code_response(code_title: str, description: str, closing_message: str) -> str:
    """Generate a code response with the given title, description, and closing message."""
    return f"""\
{description}

```python
# {code_title}

def fibonacci(n):
    \"\"\"Generate Fibonacci sequence up to n terms.\"\"\"
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence

# Example usage
if __name__ == "__main__":
    result = fibonacci(10)
    print(f"First 10 Fibonacci numbers: {{result}}")
```

{closing_message}
"""


@server.agent(
    name="Canvas coding test agent",
)
async def artifacts_agent(
    input: Message,
    context: RunContext,
    canvas: Annotated[
        CanvasExtensionServer,
        CanvasExtensionSpec(),
    ],
    _e: Annotated[ErrorExtensionServer, ErrorExtensionSpec(ErrorExtensionParams(include_stacktrace=True))],
):
    """Works with artifacts"""

    await context.store(input)

    canvas_edit_request = await canvas.parse_canvas_edit_request(message=input)

    if canvas_edit_request:
        original_code = (
            canvas_edit_request.artifact.parts[0].root.text
            if isinstance(canvas_edit_request.artifact.parts[0].root, TextPart)
            else ""
        )
        edited_part = original_code[canvas_edit_request.start_index : canvas_edit_request.end_index]

        print("Canvas Edit Request:")
        print(f"Start Index: {canvas_edit_request.start_index}")
        print(f"End Index: {canvas_edit_request.end_index}")
        print(f"Artifact ID: {canvas_edit_request.artifact.artifact_id}")
        print(f"Edited part: {edited_part}")

        description = f"You requested to edit this part:\n\n~~~\n{edited_part}\n~~~"
        code_title = "Edited Code"
        closing_message = "Your code has been updated!"
    else:
        code_title = random.choice(CODE_TITLES)
        description = "Here's your code:"
        closing_message = "Happy coding!"

    response = generate_code_response(code_title, description, closing_message)

    print("Generated Response:")
    print(response)

    match = re.compile(r"```python\n(.*?)\n```", re.DOTALL).search(response)

    if not match:
        yield response
        return

    await asyncio.sleep(1)

    if pre_text := response[: match.start()]:
        message = AgentMessage(text=pre_text)
        yield message
        await context.store(message)

    await asyncio.sleep(1)

    # Keep the full match including the code block formatting
    code_content = match.group(0).strip()

    # Extract artifact name from the comment line if present
    first_line = match.group(1).strip().split("\n", 1)[0]
    artifact_name = first_line.lstrip("# ").strip() if first_line.startswith("#") else "Python Script"

    # Split code content into x chunks for streaming
    num_chunks = 8
    content_length = len(code_content)
    chunk_size = content_length // num_chunks
    chunks = []

    for i in range(num_chunks):
        start = i * chunk_size
        # Last chunk gets any remaining characters
        end = content_length if i == num_chunks - 1 else (i + 1) * chunk_size
        chunks.append(code_content[start:end])

    artifact = AgentArtifact(
        name=artifact_name,
        parts=[TextPart(text=code_content)],
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
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8008)))
