# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

"""
Example demonstrating connector management in the AgentStack SDK.

This example shows how to:
- Create connectors
- List available connector presets
- Connect/disconnect connectors with OAuth authentication
- List connector presets
"""

import asyncio
import logging

from agentstack_sdk.platform.connector import Connector, ConnectorState

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def cleanup_example_connector(url: str):
    """Helper function to clean up any existing example connectors."""
    connectors = await Connector.list()
    for connector in connectors.items:
        if connector.url.unicode_string().rstrip("/") == url.rstrip("/"):
            logger.info(f"Cleaning up existing connector: {connector.url} - {connector.id}")
            await Connector.delete(connector.id)
            await connector.wait_for_deletion()


async def example_basic_operations():
    """Demonstrate basic connector CRUD operations."""
    example_url = "https://mcp.example.com"

    await cleanup_example_connector(example_url)

    # Create a connector
    connector = await Connector.create(
        url=example_url,
        client_id="example_client_id",
        client_secret="example_client_secret",
        metadata={"key": "value"},
    )

    # Read the connector, all possibilities of input
    connector = await connector.get()
    connector = await Connector.get(connector.id)
    connector = await Connector.get(str(connector.id))

    # List all connectors
    logger.info("Connectors list:")
    connectors = await Connector.list()
    for connector in connectors.items:
        logger.info(f"{connector.id}: {connector.url} ({connector.state})")

    # delete the connector
    await connector.delete()

    # List all connectors after deletion
    result = await Connector.list()

    logger.info("Connectors after example connector deletion:")
    for conn in result.items:
        logger.info(f"{conn.id}: {conn.url} ({conn.state})")


async def example_oauth_flow():
    """Demonstrate OAuth authentication flow."""

    # Use some existing functioning URL, this one will fail
    example_url = "https://mcp-oauth-example.com"
    await cleanup_example_connector(example_url)

    connector = await Connector.create(url=example_url)

    # Connect with OAuth
    connector = await connector.connect()
    logger.info(f"Connector state: {connector.state}")

    connector = await connector.wait_for_state(state=ConnectorState.connected)
    logger.info(f"Connector state after wait: {connector.state}")

    connector = await connector.disconnect()
    logger.info(f"Connector state after disconnect: {connector.state}")

    await connector.delete()


async def example_presets():
    """Demonstrate listing available connector presets."""
    # List presets
    presets_result = await Connector.presets()

    for item in presets_result.items:
        print(f"{item}\n")


async def main():
    """Run all examples."""
    try:
        # Note:
        # - These examples assume the AgentStack server is running and you have proper authentication set up.
        # - Repalce the example URLs and credentials with valid ones for your setup.

        # Uncomment the examples you want to run:

        # await example_basic_operations()
        # await example_oauth_flow()
        # await example_presets()

        print("\nTo run the examples, uncomment them in the main() function")
        print("and ensure the AgentStack server is running with proper authentication.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
