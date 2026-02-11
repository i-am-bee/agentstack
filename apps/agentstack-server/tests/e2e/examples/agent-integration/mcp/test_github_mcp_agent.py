# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
import json
import socket
import time
from contextlib import closing
from threading import Thread

import pytest
import uvicorn
from a2a.client.helpers import create_text_message_object
from a2a.types import TaskState
from agentstack_sdk.a2a.extensions.services.mcp import (
    MCPFulfillment,
    MCPServiceExtensionClient,
    MCPServiceExtensionSpec,
    StreamableHTTPTransport,
)
from mcp.server.fastmcp import FastMCP

from tests.e2e.examples.conftest import run_example

pytestmark = pytest.mark.e2e

MOCK_GET_ME_RESPONSE = {
    "login": "test-user",
    "id": 12345,
    "name": "Test User",
    "email": "test@example.com",
    "type": "User",
}


def _create_mock_mcp_server() -> FastMCP:
    mcp = FastMCP("mock-github-mcp")

    @mcp.tool()
    def get_me() -> str:
        """Get the authenticated user."""
        return json.dumps(MOCK_GET_ME_RESPONSE)

    return mcp


@pytest.fixture()
def mock_mcp_server_url():
    """Start a mock MCP server on a free port and yield its StreamableHTTP URL."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        port = int(sock.getsockname()[1])

    mcp = _create_mock_mcp_server()
    app = mcp.streamable_http_app()

    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    def run_server():
        with contextlib.suppress(KeyboardInterrupt):
            server.run()

    thread = Thread(target=run_server, name="mock-mcp-server", daemon=True)
    thread.start()

    while not server.started:
        time.sleep(0.1)

    yield f"http://127.0.0.1:{port}/mcp"

    server.should_exit = True
    thread.join(timeout=5)


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_github_mcp_agent_example(subtests, get_final_task_from_stream, a2a_client_factory, mock_mcp_server_url):
    example_path = "agent-integration/mcp/github-mcp-agent"

    async with run_example(example_path, a2a_client_factory) as running_example:
        mcp_spec = MCPServiceExtensionSpec.from_agent_card(running_example.provider.agent_card)
        mcp_client = MCPServiceExtensionClient(mcp_spec)
        metadata = mcp_client.fulfillment_metadata(
            mcp_fulfillments={
                "default": MCPFulfillment(
                    transport=StreamableHTTPTransport(url=mock_mcp_server_url),
                )
            }
        )

        with subtests.test("agent calls get_me tool and returns result"):
            message = create_text_message_object(content="Get my GitHub profile")
            message.metadata = metadata
            message.context_id = running_example.context.id

            task = await get_final_task_from_stream(running_example.client.send_message(message))

            assert task.status.state == TaskState.completed
            result_text = task.history[-1].parts[0].root.text
            assert "test-user" in result_text
