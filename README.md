<h1 align="center">
  Agent Stack
</h1>

<div align="center">

[![Apache 2.0](https://img.shields.io/badge/Apache%202.0-License-EA7826?style=plastic&logo=apache&logoColor=white)](https://github.com/i-am-bee/beeai-framework?tab=Apache-2.0-1-ov-file#readme)
[![Follow on Bluesky](https://img.shields.io/badge/Follow%20on%20Bluesky-0285FF?style=plastic&logo=bluesky&logoColor=white)](https://bsky.app/profile/beeaiagents.bsky.social)
[![Join our Discord](https://img.shields.io/badge/Join%20our%20Discord-7289DA?style=plastic&logo=discord&logoColor=white)](https://discord.com/invite/NradeA6ZNF)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-0072C6?style=plastic&logo=linuxfoundation&logoColor=white)](https://lfaidata.foundation/projects/)
[![Docs](https://img.shields.io/badge/Docs-Read%20the%20Docs-0285FF?style=plastic&logo=bookstack&logoColor=white)](https://agentstack.beeai.dev)


</div>

<h4 align="center">Open infrastructure for turning AI agents into running services in minutes. </h4>

<p align="center">
    <a href="#key-features"><b>Key Features</b></a> •
    <a href="#quickstart"><b>Quickstart</b></a> •
    <a href="#reference-agents"><b>Reference Agents</b></a> •
</p>

<div align="center">

</div>

<p align="center"><em> Build agents → run them as services → call them from your app. </em></p>

---

Agent Stack is open infrastructure for turning AI agents into running services in minutes. Run agents locally or in your environment, wire them into your app over HTTP, and ship agent-powered features without building deployment infrastructure from scratch. Built on the [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/) and hosted by the **Linux Foundation**, Agent Stack ensures you aren't locked into a proprietary vendor's ecosystem.

If you’re building agent-powered features or want your agents to run outside a prototype, Agent Stack gives you a fast path from code to deployment-ready service by providing LLM routing, vector storage, authentication, file handling, deployment tooling, and more out of the box.


|   |  |
|:---------|:-------------|
| 🎯 <b>Run agents as services</b> | Expose agents over HTTP for consumption in real applications and call them like any other backend service |
| 🔄 <b>Fast local dev loop</b> | Spin up agents locally and iterate quickly |
| 🔧 <b>No agent rewrites</b> | Wrap existing agents and run them as-is |
| 🚀 <b>Deployment-ready architecture</b> | The same agents can move from local to deployed environments |

---

## Core Capabilities

| Component | What's Included |
|---------|--------------|
| **Agent Runtime** | - Self-hostable server to run agents in production |
| **LLM & AI Services** | - LLM service with support for 15+ providers (Anthropic, OpenAI, watsonx.ai, Ollama) <br>- Embeddings and vector search for RAG and semantic search |
| **Agent Deployment & Management** | - CLI for deploying, updating, and managing agents |
| **Storage & Documents** | - S3-compatible file storage for uploads and downloads<br>- Document text extraction via Docling |
| **Interfaces & Tooling** | - Out-of-the-box Web UI for testing and sharing agents<br>- Client SDK for building custom UIs and applications |
| **Integrations** | - External integrations via MCP protocol (APIs, Slack, Google Drive, etc.) with OAuth |
| **Security** | - Secrets management for API keys and credentials<br>- OAuth support for secure external integrations  |
| **Agent Stack Deployment** | - Helm chart for Kubernetes with customizable storage, databases, and authentication |
| **Framework Interoperability** | - Build agents using LangGraph, CrewAI, or your own framework<br>- All agents are automatically exposed as A2A-compatible agents for interoperability<br>- SDK handles runtime service requests and agent-to-agent communication |

> **Note**: Agent Stack ships with fully functional defaults to get you running quickly. Every component is modular and can be replaced to integrate with your organization’s existing services, providers, and infrastructure.



## Quickstart

### Installation

```sh
sh -c "$(curl -LsSf https://raw.githubusercontent.com/i-am-bee/agentstack/install/install.sh)"
```

> [!TIP]
> The one-line script works on Linux and macOS. For manual setup or experimental Windows support, see the [quickstart guide](https://agentstack.beeai.dev/introduction/quickstart).

### Usage

```sh
agentstack ui                           # Launch web interface
agentstack list                         # See what agents are available
agentstack run chat "Hi, who are you"   # Send a message to chat agent
agentstack run chat                     # Try interactive mode
agentstack info chat                    # View agent details
agentstack --help                       # See all options
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
> Check out [Building Agents](https://agentstack.beeai.dev/guides/building-agents) for a complete step-by-step guide to creating your first agent.

---

## Reference Agents

Reference implementations demonstrating core Agent Stack capabilities.

- [Agent Stack Showcase](https://github.com/jenna-winkler/agentstack-showcase) - Full-featured chat assistant demonstrating RequirementAgent with conditional tool use, web search (DuckDuckGo), advanced reasoning (ThinkTool), file handling (PDF/CSV/JSON), streaming, UI feature toggles, trajectory logging, and citation extraction.
- [Serper Search Agent](https://github.com/jenna-winkler/serper-search-agent) - Web search agent showing runtime secrets management (Secrets Extension), custom tool creation (SerperSearchTool), automatic query term extraction, and structured results with citations.
- [GitHub Issue Writer](https://github.com/jenna-winkler/github_issue_writer) - Single-turn workflow using the Form Extension for multi-field input, AI-enhanced issue drafting with ThinkTool, and Markdown formatting.
- [Vulnerability Agent](https://github.com/sandijean90/VulnerabilityAgent) - Single-turn workflow that scans a GitHub repository's Python dependencies for known vulnerabilities, writes remediation issues, and posts them on your behalf in the GitHub repo. Uses form extension, UI features, secret management, MCP tools, trajectory logging, and citation formatting.
- [Chat Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/chat) - Multi-turn conversational agent using RequirementAgent, ActTool for reasoning sequences, and ClarificationTool for ambiguous queries. Integrates DuckDuckGo, Wikipedia, OpenMeteo, and file tools with UnconstrainedMemory, streaming, citation extraction, and OpenTelemetry instrumentation.
- [Form Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/form) - Single-turn form interaction using Form Extension with multiple field types, customizable layouts, file uploads, validation, and structured output.
- [RAG Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/rag) - Retrieval-Augmented Generation agent supporting 12+ file formats, dynamic vector stores, semantic search (VectorSearchTool), document summaries (FileReaderTool), intelligent tool selection, and citation tracking with document URLs.
- [Canvas Agent](https://github.com/i-am-bee/agentstack/tree/main/agents/canvas) - Multi-turn artifact editing with the option to select and edit specific parts.
- [OAuth Agent](https://github.com/i-am-bee/agentstack/blob/main/apps/agentstack-sdk-py/examples/oauth.py) - OAuth Extension demo with MCP integration, browser-based authorization, secure token management, and Stripe MCP server access.
- [Dynamic Form Request Agent](https://github.com/i-am-bee/agentstack/blob/main/apps/agentstack-sdk-py/examples/form_request_agent.py) - Multi-step form workflow showing both static and dynamic form generation, where the agent conditionally requests additional input mid-conversation.
- [Flight Search 	and Visualization Agent](https://github.com/jezekra1/agentstack-workshop) - Agent that queries the Kiwi.com MCP API for flight results, requests missing parameters through the Form Extension, and optionally generates PNG or HTML route visualizations using geospatial helpers. It uses RequirementAgent to orchestrate tool calls (data validation and visualization) and streams a final answer with any generated files and citations.
- [Healthcare Agent](https://github.com/sandijean90/AgentStack-HealthcareAgent/tree/main) - A healthcare-focused agent that discovers and invokes other agents managed by Agent Stack, featuring a multi-turn workflow with context management, trajectory, and UI components.
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

We're grateful to these communities for advancing the state of agent infrastructure and interoperability.

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
