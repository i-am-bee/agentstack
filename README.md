<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/i-am-bee/beeai-platform/master/docs/logo/beeai_framework_light.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/i-am-bee/beeai-platform/master/docs/logo/beeai_framework_dark.svg">
    <img alt="BeeAI" src="https://raw.githubusercontent.com/i-am-bee/beeai-platform/master/docs/logo/beeai_framework_dark.svg" width="60"><br><br>
  </picture>
  BeeAI Platform
</h1>

<h4 align="center">Discover, run, and share agents from any framework</h4>

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
👉 [Learn more](TBD) | 🛠️ [Migration Guide](TBD)

---------------------------

<br />

**BeeAI** is an open-source platform that makes it easy to **discover**, **run**, and **share** AI agents across frameworks. Built on the [Agent Communication Protocol (ACP)](https://agentcommunicationprotocol.dev/) and hosted by the **Linux Foundation**, BeeAI bridges the gap between different agent ecosystems.

## The Problem BeeAI Solves

Teams trying to operationalize AI agents face three critical challenges:

- **Framework Fragmentation:** Different agent frameworks create silos and duplicated efforts
- **Deployment Complexity:** Each agent requires its own setup, limiting scalability
- **Discovery Challenges:** No central hub exists for finding and using available agents

BeeAI provides a standardized platform to discover, run, and share agents from any framework - for both individuals and teams.

## 👩‍💻 For Individual Developers

BeeAI makes it easy to experiment with agent capabilities on your own machine:

- 🧪 **Try agents** instantly from the community catalog without complex setup
- 📦 Use **standard interfaces** that create consistent user experiences
- 🛠️ **Package existing agents** from any framework using standardized containers
- 🌍 **Share agents** with others through a consistent web interface

## 👥 For Teams

As you scale from personal experimentation to team adoption, BeeAI grows with you:

- 🌐 **Deploy a centralized BeeAI instance** that the entire team can access
- 📚 Create a **team catalog** where developers publish and end users discover agents
- 🧰 **Standardize agent interfaces** for consistent user experiences
- 🔐 **Centrally manage** LLM connections to control costs and access

## Key Features

| Feature | How It Works | Business Value |
| :------ | :----------- | :------------- |
| **Agent Catalog** | One BeeAI platform serves your entire team | Everyone works from the same system with unified management |
| **Framework Agnostic** | BeeAI implements the Agent Communication Protocol (ACP) to standardize agent interfaces regardless of how they're built | Developers use their preferred tools while maintaining compatibility |
| **Containerized Agents** | Each agent runs in its own container with defined resource limits | Better performance, improved security, and efficient resource usage |
| **Consistent Interfaces** | Predictable agent interactions | Learn once, use everywhere |
| **Agent Discovery** | All agents appear in a searchable catalog with capability details | End users easily find agents and developers see usage patterns |
| **LLM Provider Flexibility** | Connect to any LLM provider | Use the best model for each task and easily switch providers |

## Quickstart

> [!TIP]
> This is the short version. See the [installation guide](https://docs.beeai.dev/introduction/installation) for detailed instructions.

1. **Install** the BeeAI CLI using [uv](https://docs.astral.sh/uv/) (on Linux you'll also need [QEMU](https://www.qemu.org/download/#linux)):

```sh
uv tool install beeai-cli
```

2. **Start** the BeeAI platform:

```sh
beeai platform start
```

3. **Configure** the LLM provider:

```sh
beeai env setup
```

4. **Use** the CLI:

```sh
# List all available agents
beeai list

# Run an agent interactively
beeai run chat

# Run an agent with direct input
beeai run chat "Hello! How are you?"

# Get agent details and parameters
beeai info chat

# View all CLI options
beeai --help
```

5. **Launch** the web interface:

```sh
beeai ui
```

> [!NOTE]
> The web UI is intentionally simplified for end-users who need basic agent interactions without CLI complexity. Think of the web UI as a deployment target for your agents, not your primary development environment.

## Documentation

Visit [docs.beeai.dev](https://docs.beeai.dev) for full documentation.

## Agent Catalog

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
