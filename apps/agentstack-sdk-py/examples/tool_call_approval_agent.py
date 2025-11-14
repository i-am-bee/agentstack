# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from a2a.types import Message
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

from agentstack_sdk.a2a.extensions.tools.call import (
    ToolCallExtensionParams,
    ToolCallExtensionServer,
    ToolCallExtensionSpec,
    ToolCallRequest,
)
from agentstack_sdk.a2a.extensions.tools.exceptions import ToolCallRejectionError
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def tool_call_approval_agent(
    message: Message,
    context: RunContext,
    mcp_tool_call: Annotated[ToolCallExtensionServer, ToolCallExtensionSpec(params=ToolCallExtensionParams())],
):
    async with (
        streamablehttp_client(url="https://hf.co/mcp") as (read, write, _),
        ClientSession(read, write) as session,
    ):
        session_init_result = await session.initialize()

        list_tools_result = await session.list_tools()
        tools = {tool.name: tool for tool in list_tools_result.tools}

        whoami_tool = tools.get("hf_whoami")
        if not whoami_tool:
            raise RuntimeError("Could not find whoami_tool on the server")

        arguments = {}
        try:
            await mcp_tool_call.request_tool_call_approval(
                ToolCallRequest.from_mcp_tool(whoami_tool, arguments, server=session_init_result.serverInfo),
                context=context,
            )
            result = await session.call_tool("hf_whoami", arguments)
            content = result.content[0]
            if isinstance(content, TextContent):
                yield content.text
            else:
                yield "Tool call succeeded"
        except ToolCallRejectionError:
            yield "Tool call has been rejected by the client"


if __name__ == "__main__":
    server.run()
