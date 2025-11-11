# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message
from mcp import ClientSession

from agentstack_sdk.a2a.extensions.services.mcp import MCPServiceExtensionServer, MCPServiceExtensionSpec
from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionServer, PlatformApiExtensionSpec
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def connectors_agent(
    message: Message,
    context: RunContext,
    mcp: Annotated[
        MCPServiceExtensionServer,
        MCPServiceExtensionSpec.single_demand(),
    ],
    platform: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
) -> AsyncGenerator[RunYield, Message]:
    """Lists tools"""

    if not mcp:
        yield "MCP extension hasn't been activated, no tools are available"
        return

    async with mcp.create_client() as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        tools = await session.list_tools()

        yield "Available tools: \n"
        yield "\n".join([t.name for t in tools.tools])


if __name__ == "__main__":
    server.run()
