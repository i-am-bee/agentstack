# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""
Example demonstrating connector management in the AgentStack SDK.

This example shows how to:
- Create connectors
- List available connector presets
- Connect/disconnect connectors with OAuth authentication
- Manage connector lifecycle
"""

import asyncio

from agentstack_sdk.platform.connector import Connector


async def example_basic_operations():
    """Demonstrate basic connector CRUD operations."""
    print("=== Basic Connector Operations ===\n")

    # Create a connector
    print("Creating a connector...")
    connector = await Connector.create(
        url="https://mcp.example.com",
        client_id="example_client_id",
        client_secret="example_client_secret",
        metadata={"key": "value"},
    )
    print(f"Created connector: {connector.id}")
    print(f"Status: {connector.state}\n")

    # Read the connector
    print("Reading connector details...")
    connector = await connector.get()
    print(f"Connector URL: {connector.url}")
    print(f"Current state: {connector.state}\n")

    # List all connectors
    print("Listing all connectors...")
    result = await connector.list()
    print(f"Total connectors: {result.total_count}")
    for conn in result.items:
        print(f"  - {conn.id}: {conn.url} ({conn.state})\n")


async def example_oauth_flow():
    """Demonstrate OAuth authentication flow."""
    print("=== OAuth Connection Flow ===\n")

    # Create a connector
    connector = await Connector.create(url="https://mcp-oauth.example.com")
    print(f"Created connector: {connector.id}")
    print(f"Initial state: {connector.state}\n")

    # Connect with OAuth
    print("Initiating OAuth connection...")
    updated_connector = await connector.connect()
    print(f"Updated state: {updated_connector.state}\n")

    # If auth is required, the API response includes auth_request
    if updated_connector.auth_request:
        print("Authorization required!")
        auth_url = updated_connector.auth_request.authorization_endpoint
        print(f"Authorization endpoint: {auth_url}\n")

        # In a real scenario, you would wait for OAuth callback
        print("Waiting for OAuth callback...")
        # The server handles the callback and updates the connector state

        # Check connection status
        final_connector = await connector.get()
        print(f"Final state: {final_connector.state}\n")


async def example_presets():
    """Demonstrate listing available connector presets."""
    print("=== Available Connector Presets ===\n")

    # List presets
    presets_result = await Connector.presets()
    print(f"Available presets: {presets_result.total_count}\n")

    for preset in presets_result.items:
        print(f"URL: {preset.url}")
        if preset.metadata:
            print(f"Metadata: {preset.metadata}")
        print()


async def example_with_access_token():
    """Demonstrate connecting with an existing access token."""
    print("=== Connection with Access Token ===\n")

    # Create a connector
    connector = await Connector.create(url="https://mcp-token.example.com")
    print(f"Created connector: {connector.id}\n")

    # Connect using an access token (useful for token-based flows)
    print("Connecting with access token...")
    updated_connector = await connector.connect(access_token="your_access_token_here")
    print(f"Updated state: {updated_connector.state}\n")


async def example_disconnect():
    """Demonstrate disconnecting a connector."""
    print("=== Disconnecting a Connector ===\n")

    # Create and connect a connector
    connector = await Connector.create(url="https://mcp-disconnect.example.com")
    print(f"Created connector: {connector.id}")
    print(f"Initial state: {connector.state}\n")

    # Connect it
    connected = await connector.connect()
    print(f"After connect: {connected.state}\n")

    # Disconnect it
    print("Disconnecting...")
    disconnected = await connector.disconnect()
    print(f"After disconnect: {disconnected.state}")
    if disconnected.disconnect_reason:
        print(f"Disconnect reason: {disconnected.disconnect_reason}\n")


async def example_delete():
    """Demonstrate deleting a connector."""
    print("=== Deleting a Connector ===\n")

    # Create a connector
    connector = await Connector.create(url="https://mcp-delete.example.com")
    connector_id = connector.id
    print(f"Created connector: {connector_id}\n")

    # List before deletion
    before = await connector.list()
    print(f"Connectors before deletion: {before.total_count}\n")

    # Delete the connector
    print("Deleting connector...")
    await connector.delete()
    print(f"Deleted connector: {connector_id}\n")

    # List after deletion
    after = await connector.list()
    print(f"Connectors after deletion: {after.total_count}\n")


async def example_direct_api():
    """Demonstrate using Connector class directly (lower-level API)."""
    print("=== Using Connector Class Directly ===\n")

    # Create using static method
    connector = await Connector.create(url="https://mcp-direct.example.com", match_preset=False)
    print(f"Created connector: {connector.id}\n")

    # Read using static method
    fetched = await Connector.get(connector.id)
    print(f"Fetched connector state: {fetched.state}\n")

    # List using static method
    all_connectors = await Connector.list()
    print(f"Total connectors: {all_connectors.total_count}\n")

    # Connect using instance method
    connected = await connector.connect()
    print(f"After connect: {connected.state}\n")

    # Disconnect using instance method
    disconnected = await connected.disconnect()
    print(f"After disconnect: {disconnected.state}\n")

    # Delete using instance method
    await connector.delete()
    print("Connector deleted\n")


async def main():
    """Run all examples."""
    print("AgentStack SDK - Connector Management Examples\n")
    print("=" * 50 + "\n")

    try:
        # Note: These examples assume the AgentStack server is running
        # and you have proper authentication set up.

        # Uncomment the examples you want to run:

        # await example_basic_operations()
        # await example_oauth_flow()
        # await example_presets()
        # await example_with_access_token()
        # await example_disconnect()
        # await example_delete()
        # await example_direct_api()

        print("\nTo run the examples, uncomment them in the main() function")
        print("and ensure the AgentStack server is running with proper authentication.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
