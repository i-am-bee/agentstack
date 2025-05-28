<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/i-am-bee/beeai/master/docs/logo/beeai_framework_light.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/i-am-bee/beeai/master/docs/logo/beeai_framework_dark.svg">
    <img alt="BeeAI" src="https://raw.githubusercontent.com/i-am-bee/beeai/master/docs/logo/beeai_framework_dark.svg" width="60"><br><br>
  </picture>
  BeeAI Platform
</h1>

<h4 align="center">Discover, run, and orchestrate AI agents from any framework</h4>

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

https://github.com/user-attachments/assets/dc6cc4d7-4577-44c9-acf7-ec0133268a2d

</div>

<br />

**BeeAI** is the first open-source platform built on the [Agent Communication Protocol (ACP)](https://agentcommunicationprotocol.dev/), an open standard designed to enable smooth communication between AI agents, no matter what framework they’re built on. Hosted by the **Linux Foundation**, BeeAI is driven by open governance and community collaboration.

With ACP at its core, BeeAI makes it easy to:
- **Discover** agents across a wide range of frameworks via our growing catalog
- **Run** agents locally using your preferred LLM provider
- **Orchestrate** agents into workflows — regardless of how or where they were built
​
## Key features

| Feature                 | Description                                                                                                                                                                                     |
| :---------------------  | :---------------------------------------------------------------------------------------------------------------- |
| 🏗️ **ACP Native**  | Built from the ground up around ACP as the official reference implementation for the protocol |
| 🔄 **Lifecycle Management** | Discover, install, configure, and run agents with simple commands |
| 🛠️ **Orchestration** | Connect specialized agents through standardized interfaces to create powerful workflows |
| 🔍 **Discovery**     | Browse our curated catalog of ACP-compliant agents across multiple frameworks |
| 🗂️ **Catalog**       | Access ready-to-use agents for research, content creation, coding, and more |
| 🧠 **LLM Integration** | Connect to any LLM provider (Ollama, OpenAI, Anthropic, etc.) with simple configuration |
| 💻 **Dual Interface Access** | Interact through both web UI and CLI depending on your preference |
| 🚢 **Containerized Deployment** | Run agents in isolated containers with automated resource management for consistent performance |

## Quickstart

1. **Install** BeeAI using [Homebrew](https://brew.sh/) (or see the [installation guide](https://docs.beeai.dev/introduction/installation) for other methods):

```sh
brew install i-am-bee/beeai/beeai
beeai platform start
```

2. **Configure** LLM provider:

```sh
beeai env setup
```

3. **Launch** the web interface:

```sh
beeai ui
```

4. **Use** from the terminal:

```sh
# List commands
beeai --help

# List all available agents
beeai list

# Run the chat agent
beeai run chat
```

## Documentation

Visit [docs.beeai.dev](https://docs.beeai.dev) for full documentation.

## Agent library

Visit [beeai.dev/agents](https://beeai.dev/agents) for the list of reference agent implementations.

## Community

The BeeAI community is active on [GitHub Discussions](https://github.com/i-am-bee/beeai/discussions) where you can ask questions, voice ideas, and share your projects.

To chat with other community members, you can join the BeeAI [Discord](https://discord.gg/NradeA6ZNF) server.

Please note that our [Code of Conduct](./CODE_OF_CONDUCT.md) applies to all BeeAI community channels. We strongly encourage you to read and follow it.

## Maintainers

For information about maintainers, see [MAINTAINERS.md](./MAINTAINERS.md).

## Contributing

Contributions to BeeAI are always welcome and greatly appreciated. Before contributing, please review our [Contribution Guidelines](./CONTRIBUTING.md) to ensure a smooth experience.

Special thanks to our contributors for helping us improve BeeAI.

<a href="https://github.com/i-am-bee/beeai/graphs/contributors">
  <img alt="Contributors list" src="https://contrib.rocks/image?repo=i-am-bee/beeai" />
</a>

## Acknowledgements

Special thanks to the following outstanding projects for their inspiration and influence:

- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [Language Server Protocol](https://github.com/microsoft/language-server-protocol)
- [JSON-RPC](https://www.jsonrpc.org/)
- [Natural Language Interaction Protocol](https://github.com/nlip-project)

---

Developed by contributors to the BeeAI project, this initiative is part of the [Linux Foundation AI & Data program](https://lfaidata.foundation/projects/). Its development follows open, collaborative, and community-driven practices.
