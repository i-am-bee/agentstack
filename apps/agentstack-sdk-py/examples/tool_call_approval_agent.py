# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Annotated

from a2a.types import Message
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client  # pyrefly: ignore [deprecated] -- TODO: upgrade
from mcp.types import TextContent

from agentstack_sdk.a2a.extensions.interactions.approval import (
    ApprovalExtensionParams,
    ApprovalExtensionServer,
    ApprovalExtensionSpec,
    ToolCallApprovalRequest,
)
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def tool_call_approval_agent(
    message: Message,
    context: RunContext,
    mcp_tool_call: Annotated[ApprovalExtensionServer, ApprovalExtensionSpec(params=ApprovalExtensionParams())],
):
    async with (
        # pyrefly: ignore [deprecated] -- TODO: upgrade
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
        response = await mcp_tool_call.request_approval(
            ToolCallApprovalRequest.from_mcp_tool(whoami_tool, arguments, server=session_init_result.serverInfo),
            context=context,
        )
        if response.approved:
            result = await session.call_tool("hf_whoami", arguments)
            content = result.content[0]
            if isinstance(content, TextContent):
                yield content.text
            else:
                yield "Tool call succeeded"
        else:
            yield "Tool call has been rejected by the client"


if __name__ == "__main__":
    server.run()
