<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/i-am-bee/beeai-platform/master/docs/logo/beeai_framework_light.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/i-am-bee/beeai-platform/master/docs/logo/beeai_framework_dark.svg">
    <img alt="BeeAI" src="https://raw.githubusercontent.com/i-am-bee/beeai-platform/master/docs/logo/beeai_framework_dark.svg" width="60"><br><br>
  </picture>
  BeeAI Platform
</h1>

<h4 align="center">Test, debug, and share agents with complete UIs - add trajectory, citations, forms, file uploads, and more</h4>

<div align="center">

[![Apache 2.0](https://img.shields.io/badge/Apache%202.0-License-EA7826?style=plastic&logo=apache&logoColor=white)](https://github.com/i-am-bee/beeai-framework?tab=Apache-2.0-1-ov-file#readme)
[![Follow on Bluesky](https://img.shields.io/badge/Follow%20on%20Bluesky-0285FF?style=plastic&logo=bluesky&logoColor=white)](https://bsky.app/profile/beeaiagents.bsky.social)
[![Join our Discord](https://img.shields.io/badge/Join%20our%20Discord-7289DA?style=plastic&logo=discord&logoColor=white)](https://discord.com/invite/NradeA6ZNF)
[![LF AI & Data](https://img.shields.io/badge/LF%20AI%20%26%20Data-0072C6?style=plastic&logo=linuxfoundation&logoColor=white)](https://lfaidata.foundation/projects/)

</div>

<p align="center">
    <a href="#key-features">Key Features</a> •
    <a href="#quickstart">Quickstart</a> •
    <a href="#documentation">Documentation</a> •
    <a href="#agent-catalog">Agent Catalog</a>
</p>

<div align="center">

</div>

---------------------------

## 🚀 IMPORTANT UPDATE

**ACP is now part of A2A under the Linux Foundation!**  
<br>
👉 [Learn more](https://github.com/orgs/i-am-bee/discussions/5) | 🛠️ [Migration Guide](https://github.com/i-am-bee/beeai-platform/blob/main/docs/community-and-support/acp-a2a-migration-guide.mdx)

---------------------------

<br />

BeeAI is an open-source platform that makes it easy to test, debug, and share AI agents in an interactive UI with out-of-the-box trajectory, citations, and more. Built on the [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/) and hosted by the Linux Foundation, BeeAI bridges the gap between different agent ecosystems.

## Key Features

| Feature | Description |
|:---------|:-------------|
| 🎯 Instant Agent UI | Generate a shareable front-end from your code in minutes. Focus on your agent's logic, not UI frameworks. |
| 🚀 Effortless Deployment | Go from container to production-ready. We handle database, storage, scaling, and RAG so you can focus on your agent. |
| 🔄 Multi-Provider Playground | Test across OpenAI, Anthropic, Gemini, IBM watsonx, Ollama and more. Instantly compare performance and cost to find the optimal model. |
| 🔧 Framework-Agnostic | Run agents from LangChain, CrewAI, BeeAI and more on a single platform. Enable cross-framework collaboration without rewriting your code. |

## Quickstart

### Installation

```sh
sh -c "$(curl -LsSf https://raw.githubusercontent.com/i-am-bee/beeai-platform/HEAD/install.sh)"
```

> [!TIP]
> The one-line script works on Linux and macOS. For manual setup or experimental Windows support, see the [quickstart guide](https://docs.beeai.dev/introduction/quickstart).

### Usage

```sh
beeai ui                     # Launch web interface
beeai list                   # See what agents are available
beeai run chat "Hi!"         # Send a message to chat agent
beeai run chat               # Try interactive mode
beeai info chat              # View agent details
beeai --help                 # See all options
```

### Build Your First Agent

```sh
git clone https://github.com/i-am-bee/beeai-platform-agent-starter my-agent
cd my-agent
uv run server               # Start your agent
```

Then in another terminal:
```sh
beeai run example_agent "Alice"  # Test your agent
```

You should see: "Ciao Alice!" 🎉

> [!TIP]
> Follow the [Hello World tutorial](https://docs.beeai.dev/build-agents/hello-world) for a step-by-step guide to building your first agent.

## Documentation

Visit [docs.beeai.dev](https://docs.beeai.dev) for full documentation.

## Community

The BeeAI community is active on [GitHub Discussions](https://github.com/i-am-bee/beeai/discussions) where you can ask questions, voice ideas, and share your projects.

To chat with other community members, you can join the BeeAI [Discord](https://discord.gg/NradeA6ZNF) server.

Please note that our [Code of Conduct](./CODE_OF_CONDUCT.md) applies to all BeeAI community channels. We strongly encourage you to read and follow it.

## Maintainers

For information about maintainers, see [MAINTAINERS.md](./MAINTAINERS.md).

## Contributing

Contributions to BeeAI are always welcome and greatly appreciated. Before contributing, please review our [Contribution Guidelines](./CONTRIBUTING.md) to ensure a smooth experience.

Special thanks to our contributors for helping us improve BeeAI.

<a href="https://github.com/i-am-bee/beeai-platform/graphs/contributors">
  <img alt="Contributors list" src="https://contrib.rocks/image?repo=i-am-bee/beeai-platform" />
</a>

## Acknowledgements

Special thanks to the following outstanding projects for their inspiration and influence:

- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [Language Server Protocol](https://github.com/microsoft/language-server-protocol)
- [JSON-RPC](https://www.jsonrpc.org/)
- [Natural Language Interaction Protocol](https://github.com/nlip-project)

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
