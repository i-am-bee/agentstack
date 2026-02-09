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
        title="Initializing...",
        content="Initializing...",
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(2.5)

    for i in range(1, 4):
        metadata = trajectory.trajectory_metadata(
            title=f"Doing step {i}/6",
            content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        )
        yield metadata
        await context.store(AgentMessage(metadata=metadata))
        await asyncio.sleep(0.6)

    for i in range(4, 7):
        metadata = trajectory.trajectory_metadata(
            title=f"Doing step {i}/6 - and a very long title to test UI wrapping capabilities, maybe a little longer",
            content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        )
        yield metadata
        await context.store(AgentMessage(metadata=metadata))
        await asyncio.sleep(2)

    await asyncio.sleep(2)

    metadata = trajectory.trajectory_metadata(
        title="Step with long content",
        content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))
    await asyncio.sleep(2)

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

    await asyncio.sleep(2)

    metadata = trajectory.trajectory_metadata(
        title="Test JSON rendering",
        content="""{
  "status": "success",
  "data": {
    "results": [
      {
        "id": 1,
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "role": "developer",
        "active": true
      },
      {
        "id": 2,
        "name": "Bob Smith",
        "email": "bob@example.com",
        "role": "designer",
        "active": false
      }
    ],
    "metadata": {
      "total": 2,
      "page": 1,
      "limit": 10
    }
  },
  "timestamp": "2025-11-12T14:30:00Z"
}""",
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(1)

    metadata = trajectory.trajectory_metadata(
        title="Web search", content="Querying search engines...", group_id="websearch"
    )
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(4)

    metadata = trajectory.trajectory_metadata(content="Found 8 results.", group_id="websearch")
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(1)

    metadata = trajectory.trajectory_metadata(content="Found 8 results\nAnalyzed 3/8 results", group_id="websearch")
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(2)

    metadata = trajectory.trajectory_metadata(content="Found 8 results\nAnalyzed 8/8 results", group_id="websearch")
    yield metadata
    await context.store(AgentMessage(metadata=metadata))

    await asyncio.sleep(4)

    metadata = trajectory.trajectory_metadata(
        title="Web search finished",
        content="Found 8 results\nAnalyzed 8/8 results\nExtracted key information from 8 sources",
        group_id="websearch",
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
