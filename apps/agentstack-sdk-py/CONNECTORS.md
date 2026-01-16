# Connector Management in AgentStack SDK

This document provides a comprehensive guide to using the connector management features in the AgentStack Python SDK.

## Overview

Connectors are integrations that allow agents to communicate with external services and tools. The SDK provides a complete interface for managing connector lifecycles, including:

- **CRUD Operations**: Create, read, update, and delete connectors
- **Connection Management**: Connect and disconnect connectors
- **OAuth Support**: Handle OAuth-based authentication flows
- **Preset Discovery**: Browse available connector presets

## Installation

Connectors are built into the AgentStack SDK. Simply install the SDK:

```bash
pip install agentstack-sdk
```

## Quick Start

### Basic Usage

```python
from agentstack_sdk.platform.connector import ConnectorManager
import asyncio

async def main():
    # Create a manager instance
    manager = ConnectorManager()
    
    # Create a connector
    connector = await manager.create(
        url="https://mcp.example.com"
    )
    print(f"Created connector: {connector.id}")
    
    # List all connectors
    connectors = await manager.list()
    print(f"Total connectors: {connectors.total_count}")
    
    # Read a specific connector
    conn = await manager.read(connector.id)
    print(f"Connector state: {conn.state}")
    
    # Delete when done
    await manager.delete(connector.id)

asyncio.run(main())
```

## API Reference

### ConnectorManager

The `ConnectorManager` class provides a high-level interface for connector operations.

#### Initialization

```python
from agentstack_sdk.platform import ConnectorManager, PlatformClient

# With default client
manager = ConnectorManager()

# With custom client
client = PlatformClient(auth_token="your_token")
manager = ConnectorManager(client=client)
```

#### Methods

##### `create()`

Create a new connector.

```python
connector = await manager.create(
    url="https://mcp.example.com",
    client_id="optional_client_id",
    client_secret="optional_client_secret",
    metadata={"key": "value"},
    match_preset=True
)
```

**Parameters:**
- `url` (AnyUrl | str): The connector/MCP server URL
- `client_id` (str, optional): OAuth client ID
- `client_secret` (str, optional): OAuth client secret
- `metadata` (dict, optional): Additional connector metadata
- `match_preset` (bool): Whether to match against presets (default: True)

**Returns:** `Connector` instance

---

##### `read()`

Retrieve a specific connector by ID.

```python
connector = await manager.read(connector_id)
```

**Parameters:**
- `connector_id` (UUID | str): The connector ID

**Returns:** `Connector` instance

---

##### `list()`

List all connectors for the current user.

```python
result = await manager.list()
for connector in result.items:
    print(f"{connector.id}: {connector.url} ({connector.state})")
```

**Returns:** `PaginatedResult[Connector]` with:
- `items`: List of Connector instances
- `total_count`: Total number of connectors
- `has_more`: Whether more results are available
- `next_page_token`: Token for fetching next page

---

##### `delete()`

Delete a connector.

```python
await manager.delete(connector_id)
```

**Parameters:**
- `connector_id` (UUID | str): The connector ID

---

##### `connect()`

Establish a connection for a connector (initiates authorization if needed).

```python
connector = await manager.connect(
    connector_id,
    redirect_url="https://localhost:8080/callback",
    access_token="optional_token"
)

# Check if auth is required
if connector.auth_request:
    auth_url = connector.auth_request.authorization_endpoint
    manager.open_browser(auth_url)  # Open browser for user auth
```

**Parameters:**
- `connector_id` (UUID | str): The connector ID
- `redirect_url` (AnyUrl | str, optional): OAuth redirect URL
- `access_token` (str, optional): Pre-existing access token

**Returns:** `Connector` instance with updated state

---

##### `disconnect()`

Disconnect a connector.

```python
connector = await manager.disconnect(connector_id)
print(f"Disconnect reason: {connector.disconnect_reason}")
```

**Parameters:**
- `connector_id` (UUID | str): The connector ID

**Returns:** `Connector` instance with disconnected state

---

##### `list_presets()`

List available connector presets.

```python
presets = await manager.list_presets()
for preset in presets.items:
    print(f"Preset: {preset.url}")
    if preset.metadata:
        print(f"  Metadata: {preset.metadata}")
```

**Returns:** `PaginatedResult[ConnectorPreset]`

---

##### `open_browser()` (static)

Open the default web browser for authentication.

```python
auth_url = "https://auth.example.com/oauth/authorize?..."
ConnectorManager.open_browser(auth_url)
```

**Parameters:**
- `auth_url` (str | AnyUrl): The authentication URL

---

### Connector

The `Connector` class represents a configured connector instance.

#### Properties

- `id` (UUID): Unique connector identifier
- `url` (AnyUrl): The connector/MCP server URL
- `state` (ConnectorState): Current state (created, auth_required, connected, disconnected)
- `auth_request` (AuthorizationCodeRequest, optional): Authentication details if auth is required
- `disconnect_reason` (str, optional): Reason for disconnection if applicable
- `metadata` (dict, optional): Additional metadata
- `created_at` (datetime, optional): Creation timestamp
- `updated_at` (datetime, optional): Last update timestamp

#### States

- **created**: Connector is newly created
- **auth_required**: Awaiting authorization
- **connected**: Successfully connected and authenticated
- **disconnected**: Connection was terminated

---

### Low-Level API (Direct Connector Class)

You can also use the `Connector` class directly for more control:

```python
from agentstack_sdk.platform.connector import Connector

# Create
connector = await Connector.create(
    url="https://mcp.example.com",
    client_id="client",
    client_secret="secret"
)

# Read
conn = await Connector.read(connector.id)

# List
result = await Connector.list()

# Connect
updated = await connector.connect()

# Disconnect
updated = await connector.disconnect()

# Delete
await connector.delete()
```

---

## OAuth Authentication Flow

When connecting to a connector that requires OAuth authentication, follow these steps:

```python
import asyncio
from agentstack_sdk.platform.connector import ConnectorManager

async def oauth_flow():
    manager = ConnectorManager()
    
    # 1. Create the connector
    connector = await manager.create(
        url="https://mcp-oauth.example.com"
    )
    
    # 2. Initiate connection
    conn = await manager.connect(connector.id)
    
    # 3. If auth is required, open browser for user
    if conn.auth_request:
        auth_url = conn.auth_request.authorization_endpoint
        print(f"Please authorize at: {auth_url}")
        manager.open_browser(auth_url)
        
        # Wait for user to complete authorization
        print("Waiting for authorization to complete...")
        # The server will handle the OAuth callback automatically
        
        # 4. Check the final state
        final = await manager.read(connector.id)
        if final.state == "connected":
            print("Connection successful!")
        else:
            print(f"Connection failed: {final.state}")

asyncio.run(oauth_flow())
```

## Advanced Usage

### Using a Custom PlatformClient

```python
from agentstack_sdk.platform import ConnectorManager, PlatformClient

# Create a client with custom configuration
client = PlatformClient(
    auth_token="your_token",
    base_url="https://api.example.com"
)

# Use it with the manager
manager = ConnectorManager(client=client)
connector = await manager.create(url="https://mcp.example.com")
```

### Handling Errors

```python
from httpx import HTTPStatusError

try:
    connector = await manager.read("invalid-id")
except HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Connector not found")
    else:
        print(f"Error: {e}")
```

### Bulk Operations

```python
# List and delete all connectors
result = await manager.list()
for connector in result.items:
    await manager.delete(connector.id)
    print(f"Deleted {connector.id}")
```

## Token Management

Token persistence is handled automatically by the AgentStack server. When you connect a connector with OAuth:

1. The SDK initiates the OAuth flow
2. The user authorizes the application
3. The server receives the authorization code via OAuth callback
4. The server exchanges the code for tokens
5. The server stores tokens securely

The SDK client doesn't need to manage tokens directly—they're managed server-side.

## Multi-User and Shared Connectors

### User-Based Connectors

By default, connectors are user-specific. Each user manages their own connectors:

```python
# Alice's connectors
alice_manager = ConnectorManager(client=alice_client)
alice_connectors = await alice_manager.list()  # Alice's connectors only

# Bob's connectors
bob_manager = ConnectorManager(client=bob_client)
bob_connectors = await bob_manager.list()  # Bob's connectors only
```

### Shared Service Accounts

For shared resources (e.g., team agents), consider using a shared service account:

```python
# Service account with elevated permissions
service_account_client = PlatformClient(
    auth_token="service_account_token",
    context_id="shared_service"
)

service_manager = ConnectorManager(client=service_account_client)

# All team members can use connectors managed by this account
shared_connector = await service_manager.read(connector_id)
```

> **Note**: The MCP connection mechanism (user-based vs. shared) depends on your AgentStack server configuration. Consult your administrator for details.

## Testing

The SDK includes comprehensive unit tests. To run them:

```bash
pytest tests/unit/test_connector.py -v
```

### Example Test

```python
import pytest
from agentstack_sdk.platform.connector import ConnectorManager
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_create_connector():
    # Mock the client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "url": "https://mcp.example.com",
        "state": "created",
        "auth_request": None,
        "disconnect_reason": None,
        "metadata": None
    }
    mock_client.post = AsyncMock(return_value=mock_response)
    
    # Test
    manager = ConnectorManager(client=mock_client)
    connector = await manager.create(url="https://mcp.example.com")
    
    # Assert
    assert connector.id is not None
    assert str(connector.url) == "https://mcp.example.com"
```

## Examples

For more detailed examples, see [examples/connector_management.py](examples/connector_management.py).

## Architecture Notes

### Design Principles

1. **Server-Side Heavy Lifting**: The SDK is a thin wrapper around the AgentStack API. All business logic is in the server.

2. **Stateless Operations**: SDK methods are stateless and can be called multiple times safely.

3. **Type Safety**: All operations are fully typed with Pydantic models for validation.

4. **Async-First**: All I/O operations are async, following Python best practices.

5. **Flexible Client Management**: Clients can be managed manually or automatically via context managers.

### API Endpoints

The connector module uses these API endpoints:

- `GET /api/v1/connectors/presets` - List presets
- `POST /api/v1/connectors` - Create connector
- `GET /api/v1/connectors` - List connectors
- `GET /api/v1/connectors/{id}` - Read connector
- `DELETE /api/v1/connectors/{id}` - Delete connector
- `POST /api/v1/connectors/{id}/connect` - Connect connector
- `POST /api/v1/connectors/{id}/disconnect` - Disconnect connector
- `POST /api/v1/connectors/{id}/mcp` - MCP proxy endpoint
- `GET /api/v1/connectors/oauth/callback` - OAuth callback handler

## Troubleshooting

### "Connection refused" errors

Ensure the AgentStack server is running and accessible at the configured URL:

```python
from agentstack_sdk.platform import ConnectorManager, PlatformClient

# Check your PLATFORM_URL environment variable or specify explicitly
client = PlatformClient(base_url="http://localhost:8333")
manager = ConnectorManager(client=client)
```

### Authorization errors

Verify your authentication token is valid:

```python
from agentstack_sdk.platform import User

# Test your token
user = await User.get()
print(f"Authenticated as: {user.email}")
```

### OAuth callback issues

Ensure the redirect URI matches your connector configuration and the server can reach your callback endpoint.

## Contributing

To contribute to connector functionality:

1. Update [connector.py](src/agentstack_sdk/platform/connector.py)
2. Add tests in [tests/unit/test_connector.py](tests/unit/test_connector.py)
3. Update this README with new features
4. Run tests: `pytest tests/unit/test_connector.py -v`

## License

Copyright 2025 © BeeAI a Series of LF Projects, LLC
SPDX-License-Identifier: Apache-2.0
