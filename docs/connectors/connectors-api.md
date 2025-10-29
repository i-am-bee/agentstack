# Connectors API

Related PR: https://github.com/i-am-bee/agentstack/pull/1357

This document describes the Connectors API for managing connections to remote MCP servers in Agent Stack.

## Overview

The Connectors API enables Agent Stack to securely connect to protected MCP servers using OAuth 2.1 authorization. The architecture designates:
- **Agent Stack** as the OAuth client
- **MCP servers** as resource servers
- **Authorization servers** for token issuance

## OAuth Authorization Flow

```mermaid
sequenceDiagram
    autonumber
    participant Browser as User-Agent<br/>(Browser)
    participant AgentStack as Agent Stack Platform<br/>(OAuth Client)
    participant MCPClient as Agent Stack Platform<br />(MCP Client)
    participant MCP as MCP Server<br/>(Resource Server)
    participant AS as Authorization Server

    Note over Browser,AS: Phase 1: Initial Discovery & Authentication

    Browser->>AgentStack: POST /connectors/{id}/connect<br />(optional: redirect_url in payload)
    AgentStack->>MCPClient: Probe
    MCPClient->>MCP: MCP initialize (no token)
    MCP-->>MCPClient: HTTP 401 + WWW-Authenticate header
    MCPClient-->>AgentStack: Auth required

    Note over AgentStack,MCP: Phase 2: Resource Metadata Discovery

    AgentStack->>MCP: GET /.well-known/oauth-protected-resource
    MCP-->>AgentStack: Resource metadata<br/>{authorization_servers: [...]}

    Note over AgentStack,AS: Phase 3: Authorization Server Discovery

    AgentStack->>AS: GET /.well-known/oauth-authorization-server
    AS-->>AgentStack: AS metadata<br/>(endpoints, capabilities)

    Note over AgentStack,AS: Phase 4: Dynamic Client Registration (if needed)

    alt No client_id configured
        AgentStack->>AS: POST /register<br/>{client_name, redirect_uris}
        AS-->>AgentStack: {client_id, client_secret}
    end

    Note over AgentStack,AS: Phase 5: OAuth 2.1 Authorization Grant (PKCE)

    AgentStack->>AgentStack: Generate code_verifier<br/>Generate code_challenge
    AgentStack-->>Browser: Return authorization URL
    Browser->>AS: Navigate to authorization_endpoint<br/>+ code_challenge<br/>+ resource parameter<br/>+ redirect_uri
    AS->>Browser: Display consent dialog
    Browser->>AS: Grant authorization
    AS-->>Browser: Redirect to callback URL<br/>+ authorization_code
    Browser->>AgentStack: GET /oauth/callback?code=...&state=...

    Note over AgentStack,AS: Phase 6: Token Exchange

    AgentStack->>AS: POST /token<br/>+ authorization_code<br/>+ code_verifier<br/>+ resource parameter
    AS-->>AgentStack: {access_token, refresh_token}
    AgentStack->>AgentStack: Store token in database

    Note over AgentStack,MCP: Phase 7: Protected Resource Access

    AgentStack->>MCPClient: Probe with token
    MCPClient->>MCP: MCP initialize<br/>Authorization: Bearer <access_token>
    MCP->>MCP: Validate token audience
    MCP-->>MCPClient: MCP initialized
    MCPClient-->>AgentStack: Connection successful
    AgentStack-->>Browser: Connector connected<br />(if redirect_url set in step 1, redirect to that url, even with error)

    Note over AgentStack,AS: Phase 8: Token Refresh (when needed, cron probing)

    loop Token expiration
        AgentStack->>AS: POST /token<br/>+ refresh_token
        AS-->>AgentStack: {access_token, new_refresh_token}
        AgentStack->>AgentStack: Update stored token
    end

    Note over Browser,AS: Phase 9: Disconnection & Token Revocation

    Browser->>AgentStack: POST /connectors/{id}/disconnect
    AgentStack->>AS: POST /revoke<br/>+ access_token
    AS-->>AgentStack: Token revoked
    AgentStack-->>Browser: Connector disconnected
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /connectors` | Create new connector configuration |
| `GET /connectors` | List all connectors |
| `GET /connectors/{id}` | Get connector details |
| `POST /connectors/{id}/connect` | Initiate connection & OAuth flow |
| `GET /oauth/callback` | Handle OAuth authorization callback |
| `POST /connectors/{id}/disconnect` | Revoke tokens and disconnect |
| `DELETE /connectors/{id}` | Delete connector configuration |

## Connector States

```mermaid
stateDiagram-v2
    [*] --> created: POST /connectors
    created --> auth_required: POST /connect<br/>(401 response)
    created --> connected: POST /connect<br/>(no auth needed)
    auth_required --> connected: OAuth flow complete
    auth_required --> disconnected: Auth failed
    connected --> disconnected: POST /disconnect
    connected --> auth_required: Token expired/invalid
    disconnected --> [*]
```
