# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
import json
import secrets
import socket
import time
from contextlib import closing
from threading import Thread
from uuid import uuid4

import httpx
import pytest
import uvicorn
from a2a.types import Message, Part, Role, TaskState, TextPart
from agentstack_sdk.a2a.extensions import OAuthExtensionClient, OAuthFulfillment
from agentstack_sdk.a2a.extensions.auth.oauth import OAuthExtensionSpec
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl, AnyUrl

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e

MOCK_ACCOUNT_RESPONSE = {
    "id": "acct_test123",
    "object": "account",
    "business_type": "company",
    "email": "test@example.com",
}


class MockOAuthProvider(OAuthAuthorizationServerProvider):
    """In-memory OAuth provider for testing."""

    def __init__(self):
        self.clients: dict[str, OAuthClientInformationFull] = {}
        self.codes: dict[str, AuthorizationCode] = {}
        self.tokens: set[str] = set()

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self.clients[client_info.client_id] = client_info

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        code = secrets.token_urlsafe(32)
        self.codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + 300,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
        )
        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        return self.codes.get(authorization_code)

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        token = secrets.token_urlsafe(32)
        self.tokens.add(token)
        return OAuthToken(access_token=token, token_type="bearer", expires_in=3600)

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token in self.tokens:
            return AccessToken(token=token, client_id="test", scopes=[])
        return None

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str):
        return None

    async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token, scopes: list[str]):
        raise NotImplementedError

    async def revoke_token(self, token) -> None:
        pass


@pytest.fixture()
def mock_oauth_mcp_server_url():
    """Start a mock MCP server with OAuth on a free port and yield its URL."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        port = int(sock.getsockname()[1])

    base_url = f"http://127.0.0.1:{port}"
    provider = MockOAuthProvider()

    mcp = FastMCP(
        "mock-mcp-with-oauth",
        auth_server_provider=provider,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(base_url),
            resource_server_url=AnyHttpUrl(base_url),
            client_registration_options=ClientRegistrationOptions(enabled=True),
        ),
    )

    @mcp.tool()
    def get_stripe_account_info() -> str:
        """Get Stripe account information."""
        return json.dumps(MOCK_ACCOUNT_RESPONSE)

    app = mcp.streamable_http_app()

    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    def run_server():
        with contextlib.suppress(KeyboardInterrupt):
            server.run()

    thread = Thread(target=run_server, name="mock-oauth-mcp-server", daemon=True)
    thread.start()

    while not server.started:
        time.sleep(0.1)

    yield f"{base_url}/mcp"

    server.should_exit = True
    thread.join(timeout=5)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_custom_mcp_client_with_oauth_example(
    subtests, a2a_client_factory, mock_oauth_mcp_server_url, monkeypatch
):
    monkeypatch.setenv("MCP_URL", mock_oauth_mcp_server_url)
    example_path = "agent-integration/mcp/custom-mcp-client-with-oauth"

    async with run_example(example_path, a2a_client_factory) as running_example:
        oauth_spec = OAuthExtensionSpec.from_agent_card(running_example.provider.agent_card)
        oauth_client = OAuthExtensionClient(oauth_spec)

        oauth_metadata = oauth_client.fulfillment_metadata(
            oauth_fulfillments={"default": OAuthFulfillment(redirect_uri=AnyUrl("http://localhost:9999/callback"))}
        )

        with subtests.test("agent authenticates via OAuth and calls MCP tool"):
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text="Get my Stripe account info"))],
                context_id=running_example.context.id,
                message_id=str(uuid4()),
                metadata=oauth_metadata,
            )

            # Send initial message - agent will start OAuth flow and return auth_required
            task = None
            async for event in running_example.client.send_message(message):
                if isinstance(event, tuple):
                    task, _ = event

            assert task is not None
            assert task.status.state == TaskState.auth_required

            # Parse the auth URL from the auth_required response
            auth_request = oauth_client.parse_auth_request(message=task.status.message)
            auth_url = str(auth_request.authorization_endpoint_url)

            # Visit the mock /authorize endpoint to get a redirect with an auth code
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(auth_url, follow_redirects=False)
                assert response.status_code == 302
                callback_url = response.headers["location"]

            # Send auth response back to the agent with the redirect URL containing the code
            auth_response = oauth_client.create_auth_response(
                task_id=task.id,
                redirect_uri=AnyUrl(callback_url),
            )
            auth_response.context_id = running_example.context.id

            # Agent completes OAuth token exchange, calls MCP tool, returns result
            async for event in running_example.client.send_message(auth_response):
                if isinstance(event, tuple):
                    task, _ = event

            assert task.status.state == TaskState.completed
            result_text = task.history[-1].parts[0].root.text
            assert "acct_test123" in result_text
