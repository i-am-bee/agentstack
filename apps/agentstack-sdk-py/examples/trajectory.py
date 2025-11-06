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
