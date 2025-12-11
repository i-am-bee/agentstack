# Agent Stack Server SDK

Python SDK for deploying agents to Agent Stack infrastructure.

[![PyPI version](https://img.shields.io/pypi/v/agentstack-sdk.svg?style=plastic)](https://pypi.org/project/agentstack-sdk/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=plastic)](https://opensource.org/licenses/Apache-2.0)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-0072C6?style=plastic&logo=linuxfoundation&logoColor=white)](https://lfaidata.foundation/projects/)

## Overview

The `agentstack-sdk` provides Python utilities for wrapping agents built with any framework (LangChain, CrewAI, BeeAI Framework, etc.) for deployment on Agent Stack. It handles the A2A (Agent-to-Agent) protocol implementation, platform service integration, and runtime requirements so you can focus on agent logic.

## Key Features

- **Framework-Agnostic Deployment** - Wrap agents from any framework for Agent Stack deployment
- **A2A Protocol Support** - Automatic handling of Agent-to-Agent communication
- **Platform Service Integration** - Connect to Agent Stack's managed LLM, embedding, file storage, and vector store services
- **Context Storage** - Manage data associated with conversation contexts

## Installation

```bash
uv add agentstack-sdk
```

## Quickstart

```python
import os
from a2a.types import AgentSkill, Message
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

# Initialize server
server = Server()

# Define your agent
@server.agent(
    name="My Agent",
    skills=[
        AgentSkill(
            id="my-agent-skill",
            name="My Agent",
            description="Agent description here",
            tags=["Chat"],
            examples=["Example query 1", "Example query 2"]
        )
    ],
)
async def my_agent(
    input: Message,
    context: RunContext,
):
    """Your agent logic here"""
    
    # Store incoming message
    await context.store(input)
    
    # Extract user message
    user_msg = "".join(
        part.root.text for part in input.parts 
        if part.root.kind == "text"
    )
    
    # Process and yield response
    response_text = f"You said: {user_msg}"
    yield response_text
    
    # Store response in context
    from agentstack_sdk.a2a.types import AgentMessage
    await context.store(AgentMessage(text=response_text))

# Run the server
if __name__ == "__main__":
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        context_store=PlatformContextStore()
    )
```

Run the agent:

```bash
python my_agent.py
```

## Available Extensions

The SDK includes extension support for:

- **Citations** - Source attribution (`CitationExtensionServer`, `CitationExtensionSpec`)
- **Trajectory** - Agent decision logging (`TrajectoryExtensionServer`, `TrajectoryExtensionSpec`)
- **Settings** - User-configurable agent parameters (`SettingsExtensionServer`, `SettingsExtensionSpec`)
- **LLM Services** - Platform-managed language models (`LLMServiceExtensionServer`, `LLMServiceExtensionSpec`)
- **Agent Details** - Metadata and UI enhancements (`AgentDetail`)
- **And more** - See [Documentation](https://agentstack.beeai.dev/stable/agent-development/overview).

Each extension provides both server-side handlers and A2A protocol specifications for seamless integration with Agent Stack's UI and infrastructure.

## Resources

- [Agent Stack Documentation](https://agentstack.beeai.dev)
- [GitHub Repository](https://github.com/i-am-bee/agentstack)
- [PyPI Package](https://pypi.org/project/agentstack-sdk/)

## Contributing

Contributions are welcome! Please see the [Contributing Guide](https://github.com/i-am-bee/agentstack/blob/main/CONTRIBUTING.md) for details.

## Support

- [GitHub Issues](https://github.com/i-am-bee/agentstack/issues)
- [GitHub Discussions](https://github.com/i-am-bee/agentstack/discussions)

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
