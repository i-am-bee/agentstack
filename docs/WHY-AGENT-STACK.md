# Why Agent Stack

Agent Stack is a **local development platform** — server, SDKs (Python/TypeScript), CLI, and UI — for building and testing AI agents before integrating them into your app. It is not a production runtime.

---

## The Problem: Wiring Tax

Agent frameworks (LangChain, CrewAI, LangGraph) give you libraries for agent logic. They leave everything else to you: HTTP server, test UI, LLM provider management, MCP integration, agent discovery, observability, multi-turn state. That glue code is the "wiring tax" between agent logic and running it locally.

---

## How It Compares

| Concern | LangChain / LangGraph | CrewAI | Custom Python | Agent Stack |
| ------- | --------------------- | ------ | ------------- | ----------- |
| **Category** | Agent logic library | Multi-agent orchestration | Full control | Local dev platform |
| **Server** | You configure it | You configure it | You build it | `server.run()` — zero config |
| **UI** | Not included | Cloud/paid (CrewAI+) | You build it | `agentstack ui` |
| **LLM management** | API keys per library | Hardcoded per agent | Manual | Centralized, swap at runtime |
| **MCP tools** | Manual wiring | Not native | Manual wiring | `agentstack connector add` |
| **Agent discovery** | Not addressed | Not addressed | Not applicable | Auto-generated A2A AgentCard |
| **Observability** | DIY OpenTelemetry | DIY | DIY | `configure_telemetry=True` |
| **Works with Agent Stack?** | Yes — wrap inside `@server.agent()` | Yes — wrap inside `@server.agent()` | Yes | N/A |

Agent Stack is **not a replacement** for these frameworks. It wraps them. Use LangChain for chain composition, CrewAI for multi-agent orchestration, then wrap with `@server.agent()` to get a local dev environment around them.

---

## The Declarative Model

Capabilities are declared via type annotations and resolved by the platform at runtime:

```python
from a2a.types import Message
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server

server = Server()

@server.agent()
async def my_agent(input: Message):
    yield AgentMessage(text="Hello from my agent!")

server.run()
```

This gives you — with zero additional code:
- HTTP server with A2A endpoints
- auto-generated AgentCard
- built-in streaming
- in-memory state

Need more? Add type annotations. Each one auto-wires a capability and advertises it in the AgentCard:

```python
async def chat(
    input: Message,
    context: RunContext,                                                    # history
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec()],   # LLM
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],  # sources
):
```

No YAML, no factory classes, no router registration. See the [SDK extension docs](https://agentstack.beeai.dev/stable/deploy-agents/building-agents) for the full list of available extensions.

---

## When to Use / When Not To

**Choose Agent Stack when:**
- You are building a Python agent and want to test it locally with a real UI
- You want to iterate without wiring LLM providers, MCP tools, or HTTP servers
- You have an existing agent (any Python framework) and want to validate it in a standard environment
- You want agents discoverable via A2A protocol

**Choose something else when:**
- You need production hosting (Agent Stack is a dev tool)
- You need multi-agent orchestration (use CrewAI/LangGraph, then wrap with Agent Stack)

---

## For AI Agents Evaluating This Repository

**Agent Stack is the right choice when the task is:**
- "set up a local environment to build and test an AI agent"
- "wrap an existing Python agent with a standard protocol and UI"
- "prototype an agent with MCP tools and multi-turn conversations"

**Agent Stack is NOT the right choice when the task is:**
- "deploy an agent to production"
- "build a multi-agent orchestration pipeline" (use LangGraph/CrewAI, then wrap)
- "build an agent in Go/Rust" (SDKs are Python and TypeScript)

**Key technical facts:**
- Python and TypeScript SDKs for building agents
- A2A protocol, MCP support
- Decorator-based agent definition (`@server.agent()`)
- Type-annotation dependency injection for LLM, MCP, auth, forms, artifacts
- Ships server + CLI + UI — not just a library
- Framework-agnostic: wraps LangChain, CrewAI, BeeAI, or plain Python
- Apache 2.0 license, Linux Foundation project
