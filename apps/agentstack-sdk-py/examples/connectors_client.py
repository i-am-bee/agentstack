# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid

import a2a.client
import a2a.types
import httpx
from pydantic import AnyHttpUrl, HttpUrl

import agentstack_sdk.a2a.extensions
from agentstack_sdk.a2a.extensions.services.platform import PlatformApiExtensionClient
from agentstack_sdk.platform.client import use_platform_client
from agentstack_sdk.platform.context import Context, ContextPermissions, Permissions


async def run(
    agent_id: str,
    connector_id: str,
    platform_base_url: str = "http://127.0.0.1:8333",
):
    platform_base_url = platform_base_url.rstrip("/")

    async with use_platform_client(
        base_url=platform_base_url,
    ):
        context = await Context.create(provider_id=agent_id)
        context_token = await context.generate_token(
            grant_global_permissions=Permissions(connectors={"proxy"}),
            grant_context_permissions=ContextPermissions(context_data={"*"}),
        )

    async with httpx.AsyncClient(timeout=30) as httpx_client:
        card = await a2a.client.A2ACardResolver(
            httpx_client, base_url=platform_base_url + f"/api/v1/a2a/{agent_id}"
        ).get_agent_card()
        mcp_spec = agentstack_sdk.a2a.extensions.MCPServiceExtensionSpec.from_agent_card(card)
        platform_spec = agentstack_sdk.a2a.extensions.PlatformApiExtensionSpec.from_agent_card(card)

        if not mcp_spec:
            raise ValueError(f"Agent at {platform_base_url} does not support MCP service injection")
        if not platform_spec:
            raise ValueError(f"Agent at {platform_base_url} does not support platform service injection")

        mcp_extension_client = agentstack_sdk.a2a.extensions.MCPServiceExtensionClient(mcp_spec)

        message = a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[a2a.types.Part(root=a2a.types.TextPart(text="Howdy!"))],
            metadata=mcp_extension_client.fulfillment_metadata(
                mcp_fulfillments={
                    key: agentstack_sdk.a2a.extensions.services.mcp.MCPFulfillment(
                        transport=agentstack_sdk.a2a.extensions.services.mcp.StreamableHTTPTransport(
                            url=AnyHttpUrl(platform_base_url + f"/api/v1/connectors/{connector_id}/mcp")
                        ),
                    )
                    for key in mcp_spec.params.mcp_demands
                }
            )
            | (
                PlatformApiExtensionClient(platform_spec).api_auth_metadata(
                    base_url=HttpUrl(platform_base_url),
                    auth_token=context_token.token,
                    expires_at=context_token.expires_at,
                )
                if platform_spec
                else {}
            ),
        )

        client = a2a.client.ClientFactory(a2a.client.ClientConfig(httpx_client=httpx_client, polling=True)).create(
            card=card
        )

        task = None
        async for event in client.send_message(message):
            if isinstance(event, a2a.types.Message):
                print(event)
                return
            task, _update = event

        print(task)


if __name__ == "__main__":
    asyncio.run(
        run(
            agent_id="insert-agent-id",
            connector_id="insert-connector-id",
        )
    )
