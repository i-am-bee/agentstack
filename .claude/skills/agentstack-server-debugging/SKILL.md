---
name: agentstack-server-debugging
description: Instructions for debugging agentstack-server during development
---

Agentstack runs in a k3s cluster inside Lima VM. Use mise scripts for local development.

## Prerequisites

- Telepresence must be running: check with `telepresence status`
- If not running, ask user to start it

## Commands

| Action | Command |
|--------|---------|
| Start dev cluster (user should do) | `mise run agentstack-server:dev:start` |
| Run server locally (you should do) | `mise run agentstack-server:run` |
| Run CLI | `mise run agentstack-cli:run -- <command>` |
| CLI help | `mise run agentstack-cli:run -- --help` |

## Example

```bash
mise run agentstack-cli:run -- list
```
