# Agent Stack

[![Docs](https://img.shields.io/badge/docs-agentstack.beeai.dev-blue)](https://agentstack.beeai.dev/)
[![Discord](https://img.shields.io/badge/discord-join-7289da)](https://discord.gg/AZFrp3UF5k)
[![License](https://img.shields.io/github/license/i-am-bee/agentstack)](LICENSE)
[![Linux Foundation](https://img.shields.io/badge/Linux%20Foundation-member-003366)](https://www.linuxfoundation.org/)

> **Build and test AI agents locally — fast, without wiring LLMs, tools, or UI.**

Local development platform (server, SDK, CLI, UI) for prototyping and validating AI agents before integration into your app.

- **Prototype** — focus on agent logic, not setup overhead
- **Integrate** — validate locally, then embed via SDK
- **Wrap** — convert existing agents using [`agentstack-wrapper`](https://skills.sh/i-am-bee/agentstack/agentstack-wrapper)

---

## ⚡ Quickstart

```sh
sh -c "$(curl -LsSf https://agentstack.beeai.dev/install.sh)"

git clone https://github.com/i-am-bee/agentstack-starter my-agent
cd my-agent
uv run server

agentstack run example_agent "Alice"
agentstack ui
```

---

## 📦 What's included

| Category         | What you get                  |
| ---------------- | ----------------------------- |
| **Structure**    | Patterns for agents and tools |
| **Runtime**      | Run locally                   |
| **UI**           | Built-in interface            |
| **CLI**          | Run and inspect agents        |
| **LLM**          | Preconfigured providers       |
| **Integrations** | MCP connectors                |

---

## 🎯 When to use Agent Stack

Use it when you need to:

- prototype and test agents locally (UI, CLI, LLMs included)
- wrap existing agents without rewriting them
- integrate MCP tools without transport/auth wiring
- make agents discoverable via A2A

Not for: production hosting/runtime.

See details and comparison in **[Why Agent Stack](docs/WHY-AGENT-STACK.md)**.

---

## 📚 Examples

### Core

| Example                  | Highlights                   |
| ------------------------ | ---------------------------- |
| [Chat][chat]             | Multi-turn, tools, streaming |
| [RAG][rag]               | Documents, vector search     |
| [Form][form]             | Structured input, validation |
| [Canvas][canvas]         | Artifact editing             |
| [OAuth][oauth]           | Auth, secure tokens          |
| [Dynamic Form][dyn-form] | Dynamic input requests       |

### Community

| Example                         | Highlights                       |
| ------------------------------- | -------------------------------- |
| [Showcase][showcase]            | Web search, files, streaming     |
| [Serper Search][serper]         | Custom tools, structured results |
| [GitHub Issue Writer][gh-issue] | Form-driven drafting             |
| [Vulnerability Agent][vuln]     | CVE scanning, issue filing       |
| [Flight Search][flight-search]  | Flight queries, visualization    |
| [Healthcare Agent][healthcare]  | Multi-agent orchestration        |

[chat]: https://github.com/i-am-bee/agentstack/tree/main/agents/chat
[rag]: https://github.com/i-am-bee/agentstack/tree/main/agents/rag
[form]: https://github.com/i-am-bee/agentstack/tree/main/agents/form
[canvas]: https://github.com/i-am-bee/agentstack/tree/main/agents/canvas
[oauth]: https://github.com/i-am-bee/agentstack/blob/main/apps/agentstack-sdk-py/examples/oauth.py
[dyn-form]: https://github.com/i-am-bee/agentstack/blob/main/apps/agentstack-sdk-py/examples/form_request_agent.py
[showcase]: https://github.com/jenna-winkler/agentstack-showcase
[serper]: https://github.com/jenna-winkler/serper-search-agent
[gh-issue]: https://github.com/jenna-winkler/github_issue_writer
[vuln]: https://github.com/sandijean90/VulnerabilityAgent
[flight-search]: https://github.com/jezekra1/agentstack-workshop
[healthcare]: https://github.com/sandijean90/AgentStack-HealthcareAgent/tree/main

---

## 📖 Documentation

Full docs at **[agentstack.beeai.dev](https://agentstack.beeai.dev/)**:
[Quickstart](https://agentstack.beeai.dev/stable/introduction/quickstart) ·
[Build agents](https://agentstack.beeai.dev/stable/deploy-agents/building-agents) ·
[Wrap existing agents](https://agentstack.beeai.dev/stable/deploy-agents/wrap-existing-agents) ·
[Integrate into your app](https://agentstack.beeai.dev/stable/deploy-agent-stack/deployment-guide)

## 🤝 Contributing

See the [contributing guide](CONTRIBUTING.md).
[Report bugs](https://github.com/i-am-bee/agentstack/issues) ·
[Discussions](https://github.com/i-am-bee/agentstack/discussions) ·
[Discord](https://discord.gg/AZFrp3UF5k)

Agent Stack is an open-source project maintained as part of the Linux Foundation community.

## ⚖️ License

[Apache 2.0](LICENSE)
