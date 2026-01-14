# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# TODO: These tests need running agentstack test server, same as all the other e2e server tests,
#   The reason why an sdk test file is in the server tests folder is so we don't start the VM etc. twice.
#   All the e2e test should be moved to a common e2e tests folder outside of the apps folder in the future.

"""E2E tests for Connector SDK using the agentstack-sdk-py PlatformClient."""

import json
import logging

import pytest
from agentstack_sdk.platform.client import PlatformClient
from agentstack_sdk.platform.connector import Connector, ConnectorState
from httpx import HTTPStatusError

from tests.conftest import Configuration

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.e2e


@pytest.fixture
async def platform_client(test_configuration: Configuration, test_admin):
    """Create a PlatformClient configured for the test environment."""
    async with PlatformClient(base_url=test_configuration.server_url, auth=test_admin, timeout=120.0) as client:
        yield client


@pytest.mark.usefixtures("clean_up")
async def test_list_connector_presets_sdk(platform_client: PlatformClient):
    """Test listing connector presets using the SDK."""
    result = await Connector.presets(client=platform_client)

    assert result.total_count > 0, "Expected at least one preset"
    assert len(result.items) > 0, "Expected preset items"

    # Find the test MCP preset
    test_mcp_preset = next(
        (p for p in result.items if "mcp+stdio://test" in str(p.url)),
        None,
    )

    assert test_mcp_preset is not None, "Expected to find mcp+stdio://test preset"
    assert test_mcp_preset.metadata is not None
    assert test_mcp_preset.metadata.get("name") == "Test MCP Server"

    logger.info(
        "Listed %d connector presets, found test preset: %s",
        result.total_count,
        test_mcp_preset.url,
    )


@pytest.mark.usefixtures("clean_up")
async def test_stdio_connector_lifecycle_sdk(platform_client: PlatformClient):
    """Test full connector lifecycle using the SDK: create, connect, use, disconnect, delete."""

    # Use the preset URL directly - stdio connectors must match a preset
    mcp_url = "mcp+stdio://test"

    # Create connector
    connector = await Connector.create(url=mcp_url, client=platform_client)

    result = await Connector.list(client=platform_client)
    assert result.total_count > 0, "Expected at least one connector"
    assert len(result.items) > 0, "Expected connector items"
    found = any(c.url.unicode_string() == mcp_url for c in result.items)
    assert found, f"Expected to find connector {mcp_url} in list"

    try:
        _ = await Connector.create(url=mcp_url, client=platform_client)
    except HTTPStatusError as e:
        assert e.response.status_code == 409, "Expected 409 Conflict for duplicate connector creation"

    assert connector.id is not None
    assert connector.state == ConnectorState.created
    assert connector.url.unicode_string() == mcp_url
    assert connector.metadata["name"] == "Test MCP Server"

    connector_id = connector.id

    # Test all variations of get and refresh input
    connector = await connector.get(client=platform_client)
    assert connector.id == connector_id
    connector = await Connector.get(connector.id, client=platform_client)
    assert connector.id == connector_id
    connector = await Connector.get(str(connector.id), client=platform_client)
    assert connector.id == connector_id

    connector = await connector.refresh(client=platform_client)
    assert connector.id == connector_id
    connector = await Connector.refresh(connector.id, client=platform_client)
    assert connector.id == connector_id
    connector = await Connector.refresh(str(connector.id), client=platform_client)
    assert connector.id == connector_id

    # Connect to connector
    connector = await connector.connect(client=platform_client)
    connector = await connector.wait_for_state(state=ConnectorState.connected, client=platform_client)
    assert connector.state == ConnectorState.connected

    # Initialize MCP protocol via proxy
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    response_chunks = []
    async for mcp_response in connector.mcp_proxy(
        method="POST",
        headers={"Accept": "application/json, text/event-stream"},
        content=json.dumps(init_request).encode(),
        client=platform_client,
    ):
        response_chunks.append(mcp_response.chunk)

    init_response_headers = mcp_response.headers
    response_text = b"".join(response_chunks).decode()
    logger.info("MCP protocol initialized successfully: connector_id=%s", connector_id)

    # Prepare headers with session ID for subsequent requests
    session_id = init_response_headers.get("mcp-session-id")
    session_headers = {"Accept": "application/json, text/event-stream"}
    if session_id:
        session_headers["mcp-session-id"] = session_id

    # Send initialized notification
    init_notification_request = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }

    async for _ in connector.mcp_proxy(
        method="POST",
        headers=session_headers,
        content=json.dumps(init_notification_request).encode(),
        client=platform_client,
    ):
        pass  # Just consume the response

    logger.info("Sent initialized notification: connector_id=%s", connector_id)

    mcp_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }

    response_chunks = []
    async for mcp_response in connector.mcp_proxy(
        method="POST",
        headers=session_headers,
        content=json.dumps(mcp_request).encode(),
        client=platform_client,
    ):
        response_chunks.append(mcp_response.chunk)

    assert mcp_response.status_code == 200, f"Failed to list tools: {mcp_response}"

    response_text = b"".join(response_chunks).decode()
    mcp_data = json.loads(response_text.strip().removeprefix("event: message\ndata: "))
    assert "result" in mcp_data
    assert "tools" in mcp_data["result"]
    tools = mcp_data["result"]["tools"]
    assert len(tools) > 0, "Expected at least one tool from MCP server"

    tool_names = [tool["name"] for tool in tools]
    logger.info(
        "MCP tools retrieved: connector_id=%s tool_count=%d tool_names=%s",
        connector_id,
        len(tool_names),
        tool_names,
    )

    # Disconnect connector
    connector = await connector.disconnect(client=platform_client)
    connector = await connector.wait_for_state(state=ConnectorState.disconnected, client=platform_client)
    assert connector.state == ConnectorState.disconnected

    # Delete connector
    await connector.delete(client=platform_client)
    await connector.wait_for_deletion(client=platform_client)
    result = await Connector.list(client=platform_client)

    found = any(c.url == mcp_url for c in result.items)
    assert not found, f"Expected to not find connector {mcp_url} in list"
