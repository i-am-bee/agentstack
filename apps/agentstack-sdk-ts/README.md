# Agent Stack Client SDK

TypeScript/JavaScript client SDK for building applications that interact with Agent Stack agents.

[![npm version](https://img.shields.io/npm/v/agentstack-sdk.svg?style=plastic)](https://www.npmjs.com/package/agentstack-sdk)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=plastic)](https://opensource.org/licenses/Apache-2.0)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-0072C6?style=plastic&logo=linuxfoundation&logoColor=white)](https://lfaidata.foundation/projects/)

## Overview

The `agentstack-sdk` provides TypeScript and JavaScript tools for building client applications that communicate with agents deployed on Agent Stack. It includes utilities for handling the A2A (Agent2Agent) protocol, working with extensions, and calling the Agent Stack platform API.

## Key Features

- **A2A Protocol Support** - Parse agent cards and task status updates with typed utilities
- **Extension System** - Resolve service demands and UI metadata with typed helpers
- **Platform API Client** - Typed access to core platform resources
- **Type Safe Responses** - Zod validated payloads with structured API error helpers

## Installation

```bash
npm install agentstack-sdk
```

## Quickstart

```typescript
import {
  buildApiClient,
  buildLLMExtensionFulfillmentResolver,
  handleAgentCard,
  handleTaskStatusUpdate,
  TaskStatusUpdateType,
  unwrapResult,
} from "agentstack-sdk";

const api = buildApiClient({ baseUrl: "https://your-agentstack-instance.com" });

// 1. Receive an agent card and resolve metadata for service demands.
const { resolveMetadata } = handleAgentCard(agentCard);
const context = unwrapResult(await api.createContext({ provider_id: "provider-id" }));
const token = unwrapResult(
  await api.createContextToken({
    context_id: context.id,
    grant_global_permissions: { llm: ["*"], a2a_proxy: ["*"] },
  }),
);

const llmResolver = buildLLMExtensionFulfillmentResolver(api, token);
const metadata = await resolveMetadata({ llm: llmResolver });

// 2. Send a message with metadata using your A2A client.
const stream = client.sendMessageStream({
  message: {
    messageId: 'message-id',
    kind: "message",
    role: "user",
    contextId: context.id,
    parts: [{ kind: "text", text: "Hello" }],
    metadata,
  }
});

// 3. Handle task status updates.
for await (const event of stream) {
  if (event.kind === "status-update") {
    const message = event.status.message;

    if (message) {
      for (const part of message.parts) {
        if (part.kind === "text") {
          console.log("Agent:", part.text);
        }
      }

      if (message.metadata) {
        console.log("Metadata keys:", Object.keys(message.metadata));
      }
    }

    handleTaskStatusUpdate(event).forEach((result) => {
      switch (result.type) {
        case TaskStatusUpdateType.FormRequired:
          // Show form to the user
          break;
        case TaskStatusUpdateType.OAuthRequired:
          // Redirect to result.url
          break;
        case TaskStatusUpdateType.SecretRequired:
          // Prompt for secrets
          break;
        case TaskStatusUpdateType.ApprovalRequired:
          // Request approval from the user
          break;
      }
    });
  }
}
```

## Core APIs

- `buildApiClient` returns a typed API client for platform endpoints.
- `handleAgentCard` extracts extension demands and returns `resolveMetadata`.
- `handleTaskStatusUpdate` parses A2A status updates into UI actions.
- `resolveUserMetadata` builds metadata when the user submits forms, canvas edits, or approvals.
- `createAuthenticatedFetch` helps add bearer auth headers to API calls.
- `buildLLMExtensionFulfillmentResolver` matches LLM providers and returns fulfillments.
- `unwrapResult` returns the response data on success, throws an `ApiErrorException` on error

## Extensions

Service extensions (client fulfillments):

- **Embedding** - Provide embedding access (`api_base`, `api_key`, `api_model`) for RAG or search.
- **Form** - Request structured user input via forms.
- **LLM** - Resolve model access and credentials for text generation.
- **MCP** - Connect Model Context Protocol services and tools.
- **OAuth** - Provide OAuth credentials or redirect URIs.
- **Platform API** - Inject context token metadata for platform access.
- **Secrets** - Supply or request secret values securely.

UI extensions (message metadata your UI can render):

- **Agent Detail** - Show agent specific metadata and context.
- **Approval** - Ask the user to approve actions or tool calls.
- **Canvas** - Provide canvas edit requests and updates.
- **Citation** - Display inline source references.
- **Error** - Render structured error messages.
- **Form Request** - Render interactive forms in the UI.
- **Settings** - Read or update runtime configuration values.
- **Trajectory** - Render execution traces or reasoning steps.

## Documentation

- [Agent Stack Documentation](https://agentstack.beeai.dev)
- [Client SDK Overview](https://agentstack.beeai.dev/development/custom-ui/client-sdk/overview)
- [Extensions](https://agentstack.beeai.dev/development/custom-ui/client-sdk/extensions)
- [API Client](https://agentstack.beeai.dev/development/custom-ui/client-sdk/api-client)

## Resources

- [GitHub Repository](https://github.com/i-am-bee/agentstack)
- [npm Package](https://www.npmjs.com/package/agentstack-sdk)

## Contributing

Contributions are welcome! Please see the [Contributing Guide](https://github.com/i-am-bee/agentstack/blob/main/CONTRIBUTING.md) for details.

## Support

- [GitHub Issues](https://github.com/i-am-bee/agentstack/issues)
- [GitHub Discussions](https://github.com/i-am-bee/agentstack/discussions)

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
