# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import os
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.services.mcp import MCPServiceExtensionServer, MCPServiceExtensionSpec
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from mcp import ClientSession

server = Server()


@server.agent()
async def github_mcp_agent_example(
    mcp_service: Annotated[
        MCPServiceExtensionServer,
        MCPServiceExtensionSpec.single_demand(suggested=("github",)),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Show connected GitHub profile information"""

    if not mcp_service:
        yield "MCP extension hasn't been activated, no tools are available"
        return

    async with mcp_service.create_client() as client:
        if client is None:
            yield "MCP client not available."
            return

        read, write = client
        async with ClientSession(read_stream=read, write_stream=write) as session:
            _ = await session.initialize()
            me_result = await session.call_tool("get_me", {})
            result_dict = me_result.model_dump() if hasattr(me_result, "model_dump") else me_result
            yield json.dumps(result_dict, indent=2, default=str)


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
