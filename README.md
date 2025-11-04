<h1 align="center">
  Agent Stack
</h1>

<h4 align="center">Open infrastructure for deploying and sharing agents without vendor lock-in</h4>

<div align="center">

[![Apache 2.0](https://img.shields.io/badge/Apache%202.0-License-EA7826?style=plastic&logo=apache&logoColor=white)](https://github.com/i-am-bee/beeai-framework?tab=Apache-2.0-1-ov-file#readme)
[![Follow on Bluesky](https://img.shields.io/badge/Follow%20on%20Bluesky-0285FF?style=plastic&logo=bluesky&logoColor=white)](https://bsky.app/profile/beeaiagents.bsky.social)
[![Join our Discord](https://img.shields.io/badge/Join%20our%20Discord-7289DA?style=plastic&logo=discord&logoColor=white)](https://discord.com/invite/NradeA6ZNF)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-0072C6?style=plastic&logo=linuxfoundation&logoColor=white)](https://lfaidata.foundation/projects/)

</div>

<p align="center">
    <a href="#key-features">Key Features</a> •
    <a href="#quickstart">Quickstart</a> •
    <a href="#agent-catalog">Agent Catalog</a> •
    <a href="#documentation">Documentation</a>
</p>

<div align="center">

</div>

<div align="center">
  <img src="docs/images/ui-example2.png" alt="UI Example" width="650">
</div>

---

Agent Stack is open infrastructure for taking AI agents from prototype to production—no matter how you built them. It includes everything you need to make your agents usable by others: hosting, web UI, runtime services, and multi-tenancy—all without vendor lock-in.

Built on the [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/) and hosted by the **Linux Foundation**, Agent Stack bridges the gap between different agent ecosystems.

---

## Key Features

| Feature | Description |
|:---------|:-------------|
| 🎯 Instant Agent UI | Generate a shareable front-end from your code in minutes. Focus on your agent's logic, not UI frameworks. |
| 🚀 Effortless Deployment | Go from container to production-ready. We handle database, storage, scaling, and RAG so you can focus on your agent. |
| 🔄 Multi-Provider Playground | Test across OpenAI, Anthropic, Gemini, IBM watsonx, Ollama and more. Instantly compare performance and cost to find the optimal model. |
| 🔧 Framework-Agnostic | Run agents from LangChain, CrewAI, and more on a single platform. Enable cross-framework collaboration without rewriting your code. |

---

## Quickstart

### Installation

```sh
sh -c "$(curl -LsSf https://raw.githubusercontent.com/i-am-bee/agentstack/HEAD/install.sh)"
```

> [!TIP]
> The one-line script works on Linux and macOS. For manual setup or experimental Windows support, see the [quickstart guide](https://agentstack.beeai.dev/introduction/quickstart).

### Usage

```sh
agentstack ui                     # Launch web interface
agentstack list                   # See what agents are available
agentstack run chat "Hi!"         # Send a message to chat agent
agentstack run chat               # Try interactive mode
agentstack info chat              # View agent details
agentstack --help                 # See all options
```

### Build Your First Agent

```sh
git clone https://github.com/i-am-bee/agentstack-starter my-agent
cd my-agent
uv run server               # Start your agent
```

Then in another terminal:
```sh
agentstack run example_agent "Alice"  # Test your agent
```

You should see: "Ciao Alice!" 🎉

> [!TIP]
> Check out [Start Building Agents](https://agentstack.beeai.dev/introduction/start-building-agents) for a complete step-by-step guide to creating your first agent.

---

## Agent Catalog

### Reference Agents

Reference implementations demonstrating core Agent Stack capabilities.

- [BeeAI Showcase Agent](https://github.com/jenna-winkler/beeai-showcase-agent) - Full-featured chat assistant demonstrating RequirementAgent with conditional tool use, web search (DuckDuckGo), advanced reasoning (ThinkTool), file handling (PDF/CSV/JSON), streaming, UI feature toggles, trajectory logging, and citation extraction.
- [Serper Search Agent](https://github.com/jenna-winkler/serper-search-agent) - Web search agent showing runtime secrets management (Secrets Extension), custom tool creation (SerperSearchTool), automatic query term extraction, and structured results with citations.
- [GitHub Issue Writer](https://github.com/jenna-winkler/github_issue_writer) - Single-turn workflow using the Form Extension for multi-field input, AI-enhanced issue drafting with ThinkTool, and professional Markdown formatting.
- [Chat Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/chat) - Multi-turn conversational agent using RequirementAgent, ActTool for reasoning sequences, and ClarificationTool for ambiguous queries. Integrates DuckDuckGo, Wikipedia, OpenMeteo, and file tools with UnconstrainedMemory, streaming, citation extraction, and OpenTelemetry instrumentation.
- [Form Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/form) - Single-turn form interaction using Form Extension with multiple field types, customizable layouts, file uploads, validation, and structured output.
- [RAG Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/rag) - Retrieval-Augmented Generation agent supporting 12+ file formats, dynamic vector stores, semantic search (VectorSearchTool), document summaries (FileReaderTool), intelligent tool selection, and citation tracking with document URLs.
- [OAuth Agent](https://github.com/i-am-bee/agentstack/blob/main/apps/agentstack-sdk-py/examples/oauth.py) - OAuth Extension demo with MCP integration, browser-based authorization, secure token management, and Stripe MCP server access.
- [Dynamic Form Request Agent](https://github.com/i-am-bee/agentstack/blob/main/apps/agentstack-sdk-py/examples/request_form_agent.py) - Multi-step form workflow showing both static and dynamic form generation, where the agent conditionally requests additional input mid-conversation.

### Community Agents

A growing collection of community-built agents showcasing various use cases and integrations.

> [!NOTE]
> Community agents are maintained by their respective authors. Please review each agent's documentation before use.

- Coming soon! You can add your agent here via a PR to be featured.

> [!TIP]
> Before contributing, please review our [Contribution Guidelines](./CONTRIBUTING.md) to ensure a smooth experience.

---

## Documentation

Visit [agentstack.beeai.dev](https://agentstack.beeai.dev) for full documentation.

## Community

The Agent Stack community is active on [GitHub Discussions](https://github.com/i-am-bee/agentstack/discussions) where you can ask questions, voice ideas, and share your projects.

To chat with other community members, you can join the Agent Stack [Discord](https://discord.gg/NradeA6ZNF) server.

Please note that our [Code of Conduct](./CODE_OF_CONDUCT.md) applies to all Agent Stack community channels. We strongly encourage you to read and follow it.

## Maintainers

For information about maintainers, see [MAINTAINERS.md](./MAINTAINERS.md).

## Contributing

Contributions to Agent Stack are always welcome and greatly appreciated. Before contributing, please review our [Contribution Guidelines](./CONTRIBUTING.md) to ensure a smooth experience.

Special thanks to our contributors for helping us improve Agent Stack.

<a href="https://github.com/i-am-bee/agentstack/graphs/contributors">
  <img alt="Contributors list" src="https://contrib.rocks/image?repo=i-am-bee/agentstack" />
</a>

## Acknowledgements

Agent builds upon the foundations established by several pioneering projects in the agent and protocol ecosystem:

- [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/) - The open standard enabling cross-framework agent communication
- [Model Context Protocol](https://github.com/modelcontextprotocol) - Advancing how AI models interact with context
- [Language Server Protocol](https://github.com/microsoft/language-server-protocol) - Demonstrating the power of standardized tooling protocols
- [JSON-RPC](https://www.jsonrpc.org/) - The specification underlying modern RPC communication

We're grateful to these communities for advancing the state of agent infrastructure and interoperability.

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
