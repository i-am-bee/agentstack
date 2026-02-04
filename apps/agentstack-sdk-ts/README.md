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
npm install agentstack-sdk @a2a-js/sdk
```

## Quickstart

```typescript
import {
  buildApiClient,
  createAuthenticatedFetch,
  unwrapResult,
  handleAgentCard,
  handleTaskStatusUpdate,
  resolveUserMetadata,
  type TaskStatusUpdateType,
  type Fulfillments,
} from "agentstack-sdk";
import {
  ClientFactory,
  ClientFactoryOptions,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
} from "@a2a-js/sdk/client";

const baseUrl = "https://your-agentstack-instance.com";
const accessToken = "<user-access-token>";

const api = buildApiClient({
  baseUrl,
  fetch: createAuthenticatedFetch(accessToken),
});

const providers = unwrapResult(await api.listProviders());
const providerId = providers[0]?.id;

const context = unwrapResult(await api.createContext({ provider_id: providerId }));
const contextToken = unwrapResult(
  await api.createContextToken({
    context_id: context.id,
    grant_global_permissions: {
      llm: ["*"],
      embeddings: ["*"],
      a2a_proxy: ["*"],
    },
    grant_context_permissions: {
      files: ["*"],
      vector_stores: ["*"],
      context_data: ["*"],
    },
  }),
);

const fetchImpl = createAuthenticatedFetch(contextToken.token);
const factory = new ClientFactory(
  ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
    transports: [new JsonRpcTransportFactory({ fetchImpl })],
    cardResolver: new DefaultAgentCardResolver({ fetchImpl }),
  }),
);

const agentCardPath = `api/v1/a2a/${providerId}/.well-known/agent-card.json`;
const client = await factory.createFromUrl(baseUrl, agentCardPath);

const card = await client.getAgentCard();
const { resolveMetadata, demands } = handleAgentCard(card);

const selectedLlmModels: Record<string, string> = { default: "gpt-4o" };

const fulfillments: Fulfillments = {
  llm: demands.llmDemands
    ? async ({ llm_demands }) => ({
        llm_fulfillments: Object.fromEntries(
          Object.keys(llm_demands).map((key) => [
            key,
            {
              identifier: "llm_proxy",
              api_base: `${baseUrl}/api/v1/openai/`,
              api_key: contextToken.token,
              api_model: selectedLlmModels[key],
            },
          ]),
        ),
      })
    : undefined,
};

const agentMetadata = await resolveMetadata(fulfillments);

const stream = client.sendMessageStream({
  message: {
    kind: "message",
    role: "user",
    messageId: crypto.randomUUID(),
    contextId: context.id,
    parts: [{ kind: "text", text: "Hello" }],
    metadata: agentMetadata,
  }
});

let taskId: string | undefined;

for await (const event of stream) {
  switch (event.kind) {
    case "task":
      taskId = event.id;
    case "status-update":
      taskId = event.taskId;

      for (const update of handleTaskStatusUpdate(event)) {
        switch (update.type) {
          case TaskStatusUpdateType.FormRequired:
            // Render form
          case TaskStatusUpdateType.OAuthRequired:
            // Redirect to update.url
          case TaskStatusUpdateType.SecretRequired:
            // Prompt for secrets
          case TaskStatusUpdateType.ApprovalRequired:
            // Request approval
        }
      }
    case "message":
      // Render message parts and metadata
    case "artifact-update":
      // Render artifacts
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
- [Getting Started](https://agentstack.beeai.dev/stable/custom-ui/getting-started)
- [A2A Client Integration](https://agentstack.beeai.dev/stable/custom-ui/a2a-client)
- [Agent Requirements](https://agentstack.beeai.dev/stable/custom-ui/agent-requirements)
- [Platform API Client](https://agentstack.beeai.dev/stable/custom-ui/platform-api-client)

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
