# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message
from mcp import ClientSession

from beeai_sdk.a2a.extensions.services.mcp import MCPServiceExtensionServer, MCPServiceExtensionSpec
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext

server = Server()


@server.agent()
async def mcp_agent(
    message: Message,
    context: RunContext,
    mcp: Annotated[
        MCPServiceExtensionServer,
        MCPServiceExtensionSpec.single_demand(),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Lists tools"""
    # TODO mcp.is_active check

    async with mcp.create_client() as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.list_tools()
        yield f"These are the tools available to me: {[tool.name for tool in result.tools]}"


if __name__ == "__main__":
    server.run(self_registration=False)
