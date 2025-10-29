# Connectors API

Related PR: https://github.com/i-am-bee/beeai-platform/pull/1357

This document describes the Connectors API for managing connections to remote MCP servers in BeeAI Platform.

## Overview

The Connectors API enables BeeAI Platform to securely connect to protected MCP servers using OAuth 2.1 authorization. The architecture designates:
- **BeeAI Platform** as the OAuth client
- **MCP servers** as resource servers
- **Authorization servers** for token issuance

## OAuth Authorization Flow

```mermaid
sequenceDiagram
    autonumber
    participant Browser as User-Agent<br/>(Browser)
    participant BeeAI as BeeAI Platform<br/>(OAuth Client)
    participant MCPClient as BeeAI Platform<br />(MCP Client)
    participant MCP as MCP Server<br/>(Resource Server)
    participant AS as Authorization Server

    Note over Browser,AS: Phase 1: Initial Discovery & Authentication

    Browser->>BeeAI: POST /connectors/{id}/connect<br />(optional: redirect_url in payload)
    BeeAI->>MCPClient: Probe
    MCPClient->>MCP: MCP initialize (no token)
    MCP-->>MCPClient: HTTP 401 + WWW-Authenticate header
    MCPClient-->>BeeAI: Auth required

    Note over BeeAI,MCP: Phase 2: Resource Metadata Discovery

    BeeAI->>MCP: GET /.well-known/oauth-protected-resource
    MCP-->>BeeAI: Resource metadata<br/>{authorization_servers: [...]}

    Note over BeeAI,AS: Phase 3: Authorization Server Discovery

    BeeAI->>AS: GET /.well-known/oauth-authorization-server
    AS-->>BeeAI: AS metadata<br/>(endpoints, capabilities)

    Note over BeeAI,AS: Phase 4: Dynamic Client Registration (if needed)

    alt No client_id configured
        BeeAI->>AS: POST /register<br/>{client_name, redirect_uris}
        AS-->>BeeAI: {client_id, client_secret}
    end

    Note over BeeAI,AS: Phase 5: OAuth 2.1 Authorization Grant (PKCE)

    BeeAI->>BeeAI: Generate code_verifier<br/>Generate code_challenge
    BeeAI-->>Browser: Return authorization URL
    Browser->>AS: Navigate to authorization_endpoint<br/>+ code_challenge<br/>+ resource parameter<br/>+ redirect_uri
    AS->>Browser: Display consent dialog
    Browser->>AS: Grant authorization
    AS-->>Browser: Redirect to callback URL<br/>+ authorization_code
    Browser->>BeeAI: GET /oauth/callback?code=...&state=...

    Note over BeeAI,AS: Phase 6: Token Exchange

    BeeAI->>AS: POST /token<br/>+ authorization_code<br/>+ code_verifier<br/>+ resource parameter
    AS-->>BeeAI: {access_token, refresh_token}
    BeeAI->>BeeAI: Store token in database

    Note over BeeAI,MCP: Phase 7: Protected Resource Access

    BeeAI->>MCPClient: Probe with token
    MCPClient->>MCP: MCP initialize<br/>Authorization: Bearer <access_token>
    MCP->>MCP: Validate token audience
    MCP-->>MCPClient: MCP initialized
    MCPClient-->>BeeAI: Connection successful
    BeeAI-->>Browser: Connector connected<br />(if redirect_url set in step 1, redirect to that url, even with error)

    Note over BeeAI,AS: Phase 8: Token Refresh (when needed, cron probing)

    loop Token expiration
        BeeAI->>AS: POST /token<br/>+ refresh_token
        AS-->>BeeAI: {access_token, new_refresh_token}
        BeeAI->>BeeAI: Update stored token
    end

    Note over Browser,AS: Phase 9: Disconnection & Token Revocation

    Browser->>BeeAI: POST /connectors/{id}/disconnect
    BeeAI->>AS: POST /revoke<br/>+ access_token
    AS-->>BeeAI: Token revoked
    BeeAI-->>Browser: Connector disconnected
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
