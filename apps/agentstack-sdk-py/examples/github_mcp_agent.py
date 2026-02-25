# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message
from mcp import ClientSession

from agentstack_sdk.a2a.extensions.services.mcp import MCPServiceExtensionServer, MCPServiceExtensionSpec
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def github_mcp_agent(
    mcp_service: Annotated[
        MCPServiceExtensionServer,
        MCPServiceExtensionSpec.single_demand(suggested=("github",)),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Lists tools"""

    if not mcp_service:
        yield "MCP extension hasn't been activated, no tools are available"
        return

    async with mcp_service.create_client() as client:
        if client is None:
            yield "MCP client not available."
            return

        read, write = client
        async with ClientSession(read_stream=read, write_stream=write) as session:
            await session.initialize()
            me_result = await session.call_tool("get_me", {})
            result_dict = me_result.model_dump() if hasattr(me_result, "model_dump") else me_result
            yield json.dumps(result_dict, indent=2, default=str)


if __name__ == "__main__":
    server.run()
