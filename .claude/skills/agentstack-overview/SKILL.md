---
name: agentstack-overview
description: Provides basic insight into what the main goal of Agent Stack is, how it's structured, and how it can be used.
---

## Agent Stack Goal

Agent Stack is a platform that provides infrastructure for developing and running AI agents. Agent builders can wrap their agent code with the Agent Stack SDK. The SDK creates a thin HTTP wrapper that exposes the [A2A - Agent to Agent](https://a2a-protocol.org/latest/specification) protocol, which is enhanced with custom [extensions](https://a2a-protocol.org/latest/topics/extensions/).

The exposed HTTP server is then registered with the AgentStack server. The Agent Stack UI then provides a GUI (or CLI) to run the agent.

## Agent Stack Personas

### Agent Builder

Typically a Python developer who either has an existing agent implemented in any framework (e.g., BeeAI, LangGraph, CrewAI) or is building an agent from scratch. This person wants to focus on building the agent, not on the interface, integration, or authentication. Agent Stack provides a quick and functional UI for their agents that they can use for local development, testing, or sharing with others.
