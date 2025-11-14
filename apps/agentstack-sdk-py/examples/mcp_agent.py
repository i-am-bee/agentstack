# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions.auth.oauth import OAuthExtensionServer, OAuthExtensionSpec
from agentstack_sdk.a2a.extensions.mcp import MCPExtensionParams, MCPExtensionServer, MCPExtensionSpec
from agentstack_sdk.a2a.extensions.services.mcp import MCPServiceExtensionServer, MCPServiceExtensionSpec
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.mcp.session import MCPClientSession

server = Server()


@server.agent()
async def mcp_agent(
    message: Message,
    context: RunContext,
    oauth: Annotated[OAuthExtensionServer, OAuthExtensionSpec.single_demand()],
    mcp: Annotated[MCPExtensionServer, MCPExtensionSpec(params=MCPExtensionParams())],
    mcp_service: Annotated[
        MCPServiceExtensionServer,
        MCPServiceExtensionSpec.single_demand(),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Lists tools"""

    if not mcp_service:
        yield "MCP extension hasn't been activated, no tools are available"
        return

    async with (
        mcp_service.create_client() as (read, write),
        MCPClientSession(read, write, context=context).apply(mcp) as session,
    ):
        await session.initialize()

        result = await session.list_tools()

        yield "Available tools: \n"
        yield "\n".join([t.name for t in result.tools])

        if result.tools:
            tool = result.tools[0]
            yield f"Calling tool {tool.name}"
            await session.call_tool(tool.name, None)
            yield "Tool call finished"


if __name__ == "__main__":
    server.run()
