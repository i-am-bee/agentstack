# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message
from mcp import ClientSession

from agentstack_sdk.a2a.extensions.auth.oauth import OAuthExtensionServer, OAuthExtensionSpec
from agentstack_sdk.a2a.extensions.services.mcp import MCPServiceExtensionServer, MCPServiceExtensionSpec
from agentstack_sdk.a2a.extensions.tools.call import (
    ToolCallExtensionParams,
    ToolCallExtensionServer,
    ToolCallExtensionSpec,
    ToolCallRequest,
)
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def mcp_agent(
    message: Message,
    context: RunContext,
    oauth: Annotated[OAuthExtensionServer, OAuthExtensionSpec.single_demand()],
    mcp_tool_call: Annotated[ToolCallExtensionServer, ToolCallExtensionSpec(params=ToolCallExtensionParams())],
    mcp_service: Annotated[
        MCPServiceExtensionServer,
        MCPServiceExtensionSpec.single_demand(),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Lists tools"""

    if not mcp_service:
        yield "MCP extension hasn't been activated, no tools are available"
        return

    if not mcp_tool_call:
        yield "MCP Tool Call extension hasn't been activated, no approval requests will be issued"

    async with mcp_service.create_client() as client:
        if client is None:
            yield "MCP client not available."
            return

        read, write = client
        async with (
            ClientSession(read_stream=read, write_stream=write) as session,
        ):
            session_init_result = await session.initialize()

            result = await session.list_tools()

            yield "Available tools: \n"
            yield "\n".join([t.name for t in result.tools])

            if result.tools:
                tool = result.tools[0]
                input = {}
                yield f"Requesting approval for tool {tool.name}"
                if mcp_tool_call:
                    await mcp_tool_call.request_tool_call_approval(
                        ToolCallRequest.from_mcp_tool(tool, input, server=session_init_result.serverInfo),
                        context=context,
                    )
                yield f"Calling tool {tool.name}"
                await session.call_tool(tool.name, input)
                yield "Tool call finished"


if __name__ == "__main__":
    server.run()
