# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import logging

import httpx
import pytest

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up")
async def test_list_connector_presets(test_configuration, test_admin):
    async with httpx.AsyncClient(base_url=test_configuration.server_url, auth=test_admin, timeout=30.0) as client:
        response = await client.get("/api/v1/connectors/presets")
        assert response.status_code == 200, f"Failed to list presets: {response.text}"

        data = response.json()
        assert "items" in data
        presets = data["items"]

        test_mcp_preset = next(
            (p for p in presets if "mcp+stdio://test" in str(p["url"])),
            None,
        )

        assert test_mcp_preset is not None, "Expected to find mcp+stdio://test preset"
        assert test_mcp_preset["metadata"]["name"] == "Test MCP Server"


@pytest.mark.usefixtures("clean_up")
async def test_stdio_connector_happy_path(test_configuration, test_admin):
    async with httpx.AsyncClient(base_url=test_configuration.server_url, auth=test_admin, timeout=120.0) as client:
        logger.info("Creating stdio connector with URL mcp+stdio://test")
        create_response = await client.post(
            "/api/v1/connectors",
            json={
                "url": "mcp+stdio://test",
                "match_preset": True,
            },
        )
        assert create_response.status_code == 201, f"Failed to create connector: {create_response.text}"
        connector_data = create_response.json()
        connector_id = connector_data["id"]
        logger.info("Connector created: connector_id=%s state=%s", connector_id, connector_data["state"])

        assert connector_data["url"] == "mcp+stdio://test"
        assert connector_data["state"] == "created"
        assert connector_data["metadata"]["name"] == "Test MCP Server"

        logger.info("Connecting to connector: connector_id=%s", connector_id)
        connect_response = await client.post(
            f"/api/v1/connectors/{connector_id}/connect",
            json={},
        )
        assert connect_response.status_code == 200, f"Failed to connect: {connect_response.text}"
        connect_data = connect_response.json()
        logger.info("Connector connected successfully: connector_id=%s state=%s", connector_id, connect_data["state"])

        assert connect_data["state"] == "connected"

        logger.info("Initializing MCP protocol: connector_id=%s", connector_id)
        init_response = await client.post(
            f"/api/v1/connectors/{connector_id}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            },
            headers={"Accept": "application/json, text/event-stream"},
        )
        assert init_response.status_code == 200, f"Failed to initialize: {init_response.text}"
        logger.info("MCP protocol initialized successfully: connector_id=%s", connector_id)

        # Extract session ID from response headers for stateful connections
        session_id = init_response.headers.get("mcp-session-id")
        logger.info("MCP session ID: %s", session_id)

        # Prepare headers with session ID for subsequent requests
        session_headers = {"Accept": "application/json, text/event-stream"}
        if session_id:
            session_headers["mcp-session-id"] = session_id

        # Send initialized notification
        logger.info("Sending initialized notification: connector_id=%s", connector_id)
        await client.post(
            f"/api/v1/connectors/{connector_id}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
            headers=session_headers,
        )

        # List MCP tools via the proxy endpoint to verify it's working
        logger.info("Listing MCP tools: connector_id=%s", connector_id)
        mcp_response = await client.post(
            f"/api/v1/connectors/{connector_id}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
            },
            headers=session_headers,
        )
        assert mcp_response.status_code == 200, f"Failed to list tools: {mcp_response.text}"
        logger.info(f"MCP RESPONSE: {mcp_response.text}")
        mcp_data = json.loads(mcp_response.text.strip().removeprefix("event: message\ndata: "))

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

        assert len(tool_names) > 0, "Expected at least one tool from test MCP server"

        logger.info("Disconnecting connector: connector_id=%s", connector_id)
        disconnect_response = await client.post(f"/api/v1/connectors/{connector_id}/disconnect")
        assert disconnect_response.status_code == 200, f"Failed to disconnect: {disconnect_response.text}"
        logger.info("Connector disconnected successfully: connector_id=%s", connector_id)

        logger.info("Deleting connector: connector_id=%s", connector_id)
        delete_response = await client.delete(f"/api/v1/connectors/{connector_id}")
        assert delete_response.status_code == 204, f"Failed to delete: {delete_response.text}"
        logger.info("Connector deleted successfully: connector_id=%s", connector_id)
