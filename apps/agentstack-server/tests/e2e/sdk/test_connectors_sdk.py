# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# TODO: These tests need running agentstack test server, same as all the other e2e server tests,
#   The reason why an sdk test file is in the server tests folder is so we don't start the VM etc. twice.
#   All the e2e test should be moved to a common e2e tests folder outside of the apps folder in the future.

"""E2E tests for Connector SDK using the agentstack-sdk-py PlatformClient."""

import logging

import pytest
from agentstack_sdk.platform.client import PlatformClient
from agentstack_sdk.platform.connector import Connector

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.e2e


@pytest.fixture
async def platform_client(test_configuration):
    """Create a PlatformClient configured for the test environment."""
    async with PlatformClient(
        base_url=test_configuration.server_url,
        auth=("admin", "test-password"),
        timeout=120.0,
    ) as client:
        yield client


@pytest.fixture
async def platform_client_wo_auth(test_configuration):
    """Create a PlatformClient configured for the test environment."""
    async with PlatformClient(
        base_url=test_configuration.server_url,
        auth=None,
        timeout=120.0,
    ) as client:
        yield client


@pytest.mark.usefixtures("clean_up")
async def test_list_connector_presets_sdk(platform_client):
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


# @pytest.mark.usefixtures("clean_up")
# async def test_stdio_connector_lifecycle_sdk(platform_client):
#     """Test full connector lifecycle using the SDK: create, connect, use, disconnect, delete."""

#     # Create connector with unique URL to avoid conflicts
#     import time
#     unique_url = f"mcp+stdio://test?lifecycle_test={int(time.time()*1000000)}"

#     # Create connector
#     logger.info("Creating stdio connector with URL %s", unique_url)
#     connector = await Connector.create(
#         url=unique_url,
#         metadata={"name": "Test MCP Server", "test": "lifecycle"},
#         match_preset=False,  # Don't match preset since we have unique URL
#         client=platform_client,
#     )

#     assert connector.id is not None
#     assert connector.state == ConnectorState.created

#     connector_id = connector.id
#     logger.info("Connector created: connector_id=%s state=%s", connector_id, connector.state)

#     try:
#         # Connect to connector - this may timeout if MCP server is slow
#         logger.info("Connecting to connector: connector_id=%s (this may take up to 30s)", connector_id)
#         try:
#             connector = await connector.connect(client=platform_client)
#             assert connector.state == ConnectorState.connected
#             logger.info("Connector connected successfully: connector_id=%s state=%s", connector_id, connector.state)
#         except Exception as e:
#             logger.warning("Connect failed or timed out: %s. Skipping MCP operations.", e)
#             # Don't fail the test - connect timeout is a known issue with slow MCP server startup
#             pytest.skip(f"Connector.connect() timed out or failed: {e}")

#         # Initialize MCP protocol via proxy
#         logger.info("Initializing MCP protocol: connector_id=%s", connector_id)
#         init_request = {
#             "jsonrpc": "2.0",
#             "id": 1,
#             "method": "initialize",
#             "params": {
#                 "protocolVersion": "2024-11-05",
#                 "capabilities": {},
#                 "clientInfo": {"name": "test-client", "version": "1.0.0"},
#             },
#         }

#         # Collect streaming response
#         response_chunks = []
#         async for chunk in connector.mcp_proxy(
#             method="POST",
#             headers={"Accept": "application/json, text/event-stream"},
#             content=json.dumps(init_request).encode(),
#             client=platform_client,
#         ):
#             response_chunks.append(chunk)

#         response_text = b"".join(response_chunks).decode()
#         logger.info("MCP protocol initialized successfully: connector_id=%s", connector_id)

#         # Extract session ID from the response if present (in headers during actual usage)
#         # For this test, we'll proceed without session ID tracking since we're using the proxy

#         # Send initialized notification
#         logger.info("Sending initialized notification: connector_id=%s", connector_id)
#         initialized_notification = {
#             "jsonrpc": "2.0",
#             "method": "notifications/initialized",
#         }

#         notification_chunks = []
#         async for chunk in connector.mcp_proxy(
#             method="POST",
#             headers={"Accept": "application/json, text/event-stream"},
#             content=json.dumps(initialized_notification).encode(),
#             client=platform_client,
#         ):
#             notification_chunks.append(chunk)

#         # List MCP tools
#         logger.info("Listing MCP tools: connector_id=%s", connector_id)
#         tools_request = {
#             "jsonrpc": "2.0",
#             "id": 2,
#             "method": "tools/list",
#         }

#         tools_chunks = []
#         async for chunk in connector.mcp_proxy(
#             method="POST",
#             headers={"Accept": "application/json, text/event-stream"},
#             content=json.dumps(tools_request).encode(),
#             client=platform_client,
#         ):
#             tools_chunks.append(chunk)

#         tools_response_text = b"".join(tools_chunks).decode()
#         logger.info(f"MCP RESPONSE: {tools_response_text}")

#         # Parse the SSE response
#         mcp_data = json.loads(tools_response_text.strip().removeprefix("event: message\ndata: "))

#         assert "result" in mcp_data, "Expected 'result' in MCP response"
#         assert "tools" in mcp_data["result"], "Expected 'tools' in result"
#         tools = mcp_data["result"]["tools"]
#         assert len(tools) > 0, "Expected at least one tool from MCP server"

#         tool_names = [tool["name"] for tool in tools]
#         logger.info(
#             "MCP tools retrieved: connector_id=%s tool_count=%d tool_names=%s",
#             connector_id,
#             len(tool_names),
#             tool_names,
#         )

#         # Disconnect connector
#         logger.info("Disconnecting connector: connector_id=%s", connector_id)
#         connector = await connector.disconnect(client=platform_client)

#         assert connector.state == ConnectorState.disconnected
#         logger.info("Connector disconnected successfully: connector_id=%s", connector_id)

#     finally:
#         # Always try to delete connector
#         logger.info("Deleting connector: connector_id=%s", connector_id)
#         await Connector.delete(connector_id, client=platform_client)
#         logger.info("Connector deleted successfully: connector_id=%s", connector_id)


# @pytest.mark.usefixtures("clean_up")
# async def test_connector_list_and_get_sdk(platform_client):
#     """Test listing and getting connectors using the SDK."""

#     # Create a connector with unique URL to avoid 409 conflicts
#     unique_url = f"mcp+stdio://test?list_get_test={int(time.time()*1000000)}"

#     connector = await Connector.create(
#         url=unique_url,
#         metadata={"test": "list_and_get"},
#         match_preset=False,
#         client=platform_client,
#     )
#     connector_id = connector.id

#     try:
#         # List connectors
#         result = await Connector.list(client=platform_client)

#         assert result.total_count > 0, "Expected at least one connector"
#         assert len(result.items) > 0, "Expected connector items"

#         # Check that our connector is in the list
#         found = any(c.id == connector_id for c in result.items)
#         assert found, f"Expected to find connector {connector_id} in list"

#         logger.info("Listed %d connectors", result.total_count)

#         # Get specific connector
#         retrieved_connector = await Connector.get(connector_id, client=platform_client)

#         assert retrieved_connector.id == connector_id
#         assert retrieved_connector.state == ConnectorState.created

#         logger.info("Retrieved connector: connector_id=%s state=%s", connector_id, retrieved_connector.state)

#         # Test refresh method (should be equivalent to get)
#         refreshed_connector = await connector.refresh(client=platform_client)

#         assert refreshed_connector.id == connector_id
#         assert refreshed_connector.state == retrieved_connector.state

#         logger.info("Refreshed connector: connector_id=%s", connector_id)

#     finally:
#         # Clean up
#         await Connector.delete(connector_id, client=platform_client)


# @pytest.mark.usefixtures("clean_up")
# async def test_connector_with_metadata_sdk(platform_client):
#     """Test creating a connector with custom metadata using the SDK."""

#     unique_url = f"mcp+stdio://test?metadata_test={int(time.time()*1000000)}"

#     custom_metadata = {
#         "custom_key": "custom_value",
#         "environment": "test",
#     }

#     connector = await Connector.create(
#         url=unique_url,
#         metadata=custom_metadata,
#         match_preset=False,
#         client=platform_client,
#     )

#     try:
#         assert connector.id is not None
#         assert connector.metadata is not None
#         # Note: The server might merge metadata, so check that our keys are present
#         assert "custom_key" in connector.metadata or connector.metadata.get("custom_key") == "custom_value"

#         logger.info("Created connector with custom metadata: connector_id=%s", connector.id)

#     finally:
#         await Connector.delete(connector.id, client=platform_client)


# @pytest.mark.usefixtures("clean_up")
# async def test_connector_static_methods_with_id_sdk(platform_client):
#     """Test that static methods work with both Connector instances and string IDs."""

#     import time
#     unique_url = f"mcp+stdio://test?static_methods_test={int(time.time()*1000000)}"

#     # Create connector
#     connector = await Connector.create(
#         url=unique_url,
#         metadata={"test": "static_methods"},
#         match_preset=False,
#         client=platform_client,
#     )
#     connector_id = str(connector.id)

#     try:
#         # Test connect with string ID - skip if times out
#         try:
#             connected = await Connector.connect(connector_id, client=platform_client)
#             assert connected.state == ConnectorState.connected

#             # Test disconnect with instance
#             disconnected = await connected.disconnect(client=platform_client)
#             assert disconnected.state == ConnectorState.disconnected
#         except Exception as e:
#             logger.warning("Connect/disconnect test skipped due to timeout: %s", e)
#             # Continue with get/delete tests even if connect fails

#         # Test get with string ID
#         retrieved = await Connector.get(connector_id, client=platform_client)
#         assert retrieved.id == connector.id
#         assert retrieved.state == ConnectorState.disconnected

#         logger.info("Verified static methods work with both instances and string IDs")

#     finally:
#         # Test delete with string ID
#         await Connector.delete(connector_id, client=platform_client)
