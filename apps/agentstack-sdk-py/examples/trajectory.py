# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions import (
    TrajectoryExtensionServer,
    TrajectoryExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

server = Server()


@server.agent(
    name="Trajectories example agent",
)
async def example_agent(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
):
    """Agent that demonstrates conversation history access"""

    # Store the current message in the context store
    await context.store(input)

    metadata = trajectory.trajectory_metadata(
        title="Start",
        content="Initializing...",
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    metadata = trajectory.trajectory_metadata(
        title="Test Markdown rendering",
        content="""
# 🧭 Trajectory Markdown Rendering Test

This document tests **Markdown rendering** capabilities within the trajectory feature.

---

## 🧩 Section 1: Headers and Text Formatting

### Header Level 3

You should see **bold**, *italic*, and ***bold italic*** text properly rendered.  
> This is a blockquote — it should appear indented and stylized.

Need Markdown basics? Check out [Markdown Guide](https://www.markdownguide.org/basic-syntax/).

---

## 🧾 Section 2: Lists

### Unordered List
- Apple 🍎 — [Learn more about apples](https://en.wikipedia.org/wiki/Apple)
- Banana 🍌 — [Banana facts](https://en.wikipedia.org/wiki/Banana)
- Cherry 🍒

### Ordered List
1. First item
2. Second item
3. Third item

### Nested List
- Outer item  
  - Inner item  
    - Deep inner item

---

## 📊 Section 3: Tables

| Entity Type | Example Value     | Confidence | Reference |
|--------------|------------------|-------------|------------|
| **Name**     | Alice Johnson     | 0.97        | [Details](https://example.com) |
| **Date**     | 2025-11-12        | 0.88        | [Details](https://example.com) |
| **Location** | San Francisco, CA | 0.91        | [Details](https://example.com) |

---

## 💻 Section 4: Code Blocks

### Inline Code
You can include inline code like `const result = extractEntities(text);`.

### Fenced Code Block
```python
def extract_entities(text):
    entities = {
        "name": "Alice Johnson",
        "date": "2025-11-12",
        "location": "San Francisco"
    }
    return entities
""",
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(1)

    metadata = trajectory.trajectory_metadata(title="Searching the web", content="Searching...", group_id="websearch")
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(4)

    metadata = trajectory.trajectory_metadata(content="Found 8 results.", group_id="websearch")
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(1)

    metadata = trajectory.trajectory_metadata(content="Analyzing the results...", group_id="websearch")
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(4)

    metadata = trajectory.trajectory_metadata(
        title="Web search finished", content="Searching was successful, passing the results.", group_id="websearch"
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    # Your agent logic here - you can now reference all messages in the conversation
    message = AgentMessage(
        text="Hello! Look at the trajectories grouped in the UI! You should also find them in session history."
    )
    yield message

    # Store the message in the context store
    await context.store(message)


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), context_store=PlatformContextStore()
    )


if __name__ == "__main__":
    run()
