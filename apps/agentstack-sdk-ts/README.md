# Agent Stack Client SDK

TypeScript/JavaScript client SDK for building applications that interact with Agent Stack agents.

[![npm version](https://img.shields.io/npm/v/agentstack-sdk.svg?style=plastic)](https://www.npmjs.com/package/agentstack-sdk)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=plastic)](https://opensource.org/licenses/Apache-2.0)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-0072C6?style=plastic&logo=linuxfoundation&logoColor=white)](https://lfaidata.foundation/projects/)

## Overview

The `agentstack-sdk` provides TypeScript/JavaScript tools for building client applications that communicate with agents deployed on Agent Stack. It includes utilities for handling the A2A (Agent-to-Agent) protocol, managing agent extensions, and working with the Agent Stack platform API.

## Key Features

- **A2A Protocol Support** - Full support for Agent-to-Agent communication
- **Extension System** - Built-in handlers for forms, OAuth, LLM services, MCP, and more
- **Platform API Client** - Utilities for context and token management
- **TypeScript Types** - Comprehensive types for all APIs

## Installation

```bash
npm install agentstack-sdk
```

## Quickstart

```typescript
import { handleAgentCard, handleTaskStatusUpdate, TaskStatusUpdateType } from 'agentstack-sdk';

// Parse agent capabilities
const { extensions, fulfillments } = await handleAgentCard(agentCard);

// Send message and handle responses
const stream = client.sendMessage(message);

for await (const event of stream) {
  const result = handleTaskStatusUpdate(event);
  
  switch (result.type) {
    case TaskStatusUpdateType.Message:
      console.log('Agent response:', result.message.parts[0].text);
      break;
    case TaskStatusUpdateType.InputRequired:
      // Handle extension demands (forms, OAuth, etc.)
      break;
  }
}
```

## Available Extensions

The SDK includes clients and specs for handling:

- **Forms** - Static and dynamic form handling (`FormExtensionClient`, `FormExtensionSpec`)
- **OAuth** - Authentication flows (`OAuthExtensionClient`, `OAuthExtensionSpec`)
- **LLM Services** - Model access and credentials (`LLMServiceExtensionClient`, `buildLLMExtensionFulfillmentResolver`)
- **Platform API** - Context and resource access (`PlatformApiExtensionClient`, `buildApiClient`)
- **MCP** - Model Context Protocol integration (`MCPServiceExtensionClient`)
- **Embeddings** - Vector embedding services (`EmbeddingServiceExtensionClient`)
- **Secrets** - Secure credential management (`SecretsExtensionClient`)
- **Citations** - Source attribution (`citationExtension`)
- **Agent Details** - Metadata and UI enhancements (`AgentDetailExtensionSpec`)

Each extension has a corresponding `ExtensionClient` for sending data and `ExtensionSpec` for parsing agent cards.

## Resources

- [Agent Stack Documentation](https://agentstack.beeai.dev)
- [GitHub Repository](https://github.com/i-am-bee/agentstack)
- [npm Package](https://www.npmjs.com/package/agentstack-sdk)

## Contributing

Contributions are welcome! Please see the [Contributing Guide](https://github.com/i-am-bee/agentstack/blob/main/CONTRIBUTING.md) for details.

## Support

- [GitHub Issues](https://github.com/i-am-bee/agentstack/issues)
- [GitHub Discussions](https://github.com/i-am-bee/agentstack/discussions)

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
