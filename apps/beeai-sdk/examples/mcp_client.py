# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import uuid
import webbrowser

import a2a.client
import a2a.types
import httpx
from aiohttp import web
from pydantic import AnyHttpUrl, AnyUrl

import beeai_sdk.a2a.extensions


class OAuthHandler:
    def __init__(self, port=8080, timeout=60):
        self.redirect_uri = f"http://localhost:{port}"
        self.port = port
        self.timeout = timeout
        self.request = None
        self._server = None

    def open_browser(self, auth_url: str) -> None:
        """Open the default web browser with the provided auth_url."""
        webbrowser.open(auth_url)

    async def handle_redirect(self) -> web.Request:
        """
        Start a local server to capture the redirect URI and return the request.
        Raises TimeoutError if no redirect is received within the timeout period.
        """

        async def handler(request: web.Request) -> web.Response:
            self.request = request
            return web.Response(text="Authorization complete. You can close this window.")

        app = web.Application()
        app.router.add_get("/", handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()
        self._server = runner

        # Wait for the request or timeout
        try:
            for _ in range(int(self.timeout * 10)):  # Check every 0.1 seconds
                if self.request is not None:
                    break
                await asyncio.sleep(0.1)
            else:
                raise TimeoutError("No redirect received within the timeout period")
        finally:
            # Ensure the server is cleaned up
            await runner.cleanup()
            self._server = None

        if self.request is None:
            raise RuntimeError("No request was captured")

        return self.request


async def run(base_url: str = "http://127.0.0.1:10000"):
    async with httpx.AsyncClient(timeout=30) as httpx_client:
        card = await a2a.client.A2ACardResolver(httpx_client, base_url=base_url).get_agent_card()
        mcp_spec = beeai_sdk.a2a.extensions.MCPServiceExtensionSpec.from_agent_card(card)
        oauth_spec = beeai_sdk.a2a.extensions.OAuthExtensionSpec.from_agent_card(card)

        if not mcp_spec:
            raise ValueError(f"Agent at {base_url} does not support MCP service injection")
        if not oauth_spec:
            raise ValueError(f"Agent at {base_url} does not support oAuth")

        mcp_extension_client = beeai_sdk.a2a.extensions.MCPServiceExtensionClient(mcp_spec)
        oauth_extension_client = beeai_sdk.a2a.extensions.OAuthExtensionClient(oauth_spec)

        client = a2a.client.A2AClient(httpx_client, agent_card=card)
        oauth = OAuthHandler()
        message = a2a.types.Message(
            message_id=str(uuid.uuid4()),
            role=a2a.types.Role.user,
            parts=[a2a.types.Part(root=a2a.types.TextPart(text="Howdy!"))],
            metadata=mcp_extension_client.fulfillment_metadata(
                mcp_fulfillments={
                    key: beeai_sdk.a2a.extensions.services.mcp.MCPFulfillment(
                        transport=beeai_sdk.a2a.extensions.services.mcp.StreamableHTTPTransport(
                            url=AnyHttpUrl("https://mcp.stripe.com")
                        ),
                    )
                    for key in mcp_spec.params.mcp_demands
                }
            )
            | oauth_extension_client.fulfillment_metadata(
                oauth_fulfillments={
                    key: beeai_sdk.a2a.extensions.OAuthFulfillment(redirect_uri=AnyUrl(oauth.redirect_uri))
                    for key in oauth_spec.params.oauth_demands
                }
            ),
        )

        result = await client.send_message(
            a2a.types.SendMessageRequest(
                id=str(uuid.uuid4()),
                params=a2a.types.MessageSendParams(
                    message=message,
                    configuration=a2a.types.MessageSendConfiguration(
                        accepted_output_modes=["text"],
                    ),
                ),
            )
        )

        while True:
            if isinstance(result.root, a2a.types.JSONRPCErrorResponse):
                print(f"Error: {result.root.error}")
                return

            event = result.root.result
            if isinstance(event, a2a.types.Message):
                print(event)
                return
            elif isinstance(event, a2a.types.Task):
                if event.status.state == a2a.types.TaskState.auth_required:
                    message = event.status.message
                    if not message:
                        raise RuntimeError("Missing message")
                    auth_request = oauth_extension_client.parse_auth_request(message=message)

                    print("Agent has requested authorization")
                    oauth.open_browser(str(auth_request.authorization_endpoint_url))
                    request = await oauth.handle_redirect()

                    result = await client.send_message(
                        a2a.types.SendMessageRequest(
                            id=str(uuid.uuid4()),
                            params=a2a.types.MessageSendParams(
                                message=oauth_extension_client.create_auth_response(
                                    task_id=event.id, redirect_uri=AnyUrl(str(request.url))
                                ),
                                configuration=a2a.types.MessageSendConfiguration(
                                    accepted_output_modes=["text"],
                                ),
                            ),
                        )
                    )
                else:
                    print(event)
                    return
            else:
                raise NotImplementedError("Unexpected result type")


if __name__ == "__main__":
    asyncio.run(run())
