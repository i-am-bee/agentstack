# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

import pydantic
from agentstack_sdk.a2a.extensions.auth.oauth import OAuthExtensionServer, OAuthExtensionSpec
from agentstack_sdk.server import Server
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

server = Server()


@server.agent()
async def custom_mcp_client_with_oauth_example(
    oauth: Annotated[OAuthExtensionServer, OAuthExtensionSpec.single_demand()],
):
    """Agent that uses OAuth to authenticate with a custom MCP server"""
    mcp_url = os.getenv("MCP_URL", "https://mcp.stripe.com")

    if not oauth:
        yield "OAuth extension not available. Authentication required."
        return

    async with streamablehttp_client(
        url=mcp_url, auth=await oauth.create_httpx_auth(resource_url=pydantic.AnyUrl(mcp_url))
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_stripe_account_info")
            # Extract text content from CallToolResult
            if result.content:
                content = result.content[0]
                if hasattr(content, "text"):
                    yield str(content.text)  # type: ignore
            else:
                yield "No content returned"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
