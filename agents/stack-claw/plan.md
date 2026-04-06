# Claw-like Agent POC

Replicate OpenClaw's self-learning and self-scheduling in AgentStack using Pi SDK.

## Current State

Pi agent with conversation history, persistent workspace, self-learning, and heartbeat scheduling.

- Pi CLI (`@mariozechner/pi-coding-agent`) invoked via subprocess in RPC mode
- OpenAI LLM (`gpt-5-codex`) via `OPENAI_API_KEY` env var
- Conversation history persisted via AgentStack context (last 20 messages injected into Pi prompt)
- Per-context workspace with IDENTITY/MEMORY/DIARY/HEARTBEAT markdown files
- 60s heartbeat via `context.start_heartbeat()`
- Pi tools (`read`/`write`/`edit`/`bash`) scoped to workspace via `cwd`
- Python + `agentstack-sdk-py` for server/A2A integration

## Architecture

```
AgentStack UI conversation
        ↕ (context API)
Python agent handler (stack_claw)
        ↕
Pi agent runtime (subprocess, RPC mode)
        ↕ (built-in tools)
workspaces/<contextId>/
├── IDENTITY.md        # agent personality, evolves over time
├── MEMORY.md          # accumulated facts and learnings
├── DIARY.md           # timestamped run summaries
└── HEARTBEAT.md       # recurring task list (plain bullets)
```

Two persistence layers:
- **Conversation history** → AgentStack context API (PostgreSQL, visible in UI)
- **Self-learning artifacts** → filesystem (markdown files per context)

## Completed

### ~~1. Conversation History via AgentStack Context API~~ ✓
- User/assistant messages stored via `RunContext.store()`
- Last 20 messages formatted as `<conversation_history>` in Pi prompt
- Full history retained in AgentStack context, capped window for LLM

### ~~2. Persistent Workspace~~ ✓
- Per-context directory: `workspaces/<contextId>/`
- Seed files created on first interaction (IDENTITY, MEMORY, DIARY, HEARTBEAT)
- Pi's `cwd` set to workspace so built-in tools operate in isolation

### ~~3. Self-Learning~~ ✓
- `MEMORY.md` — agent appends facts/learnings, read at start of each run
- `DIARY.md` — timestamped summaries after tasks/heartbeats
- `IDENTITY.md` — seeded with initial instructions, agent evolves it
- Pi's built-in `read`/`write`/`edit` tools handle all file operations

### ~~4. Self-Scheduling (Heartbeat)~~ ✓
- `HEARTBEAT.md` — plain bullet list, agent reads+executes each tick
- 60s interval via `context.start_heartbeat()`
- `[heartbeat]` message prefix triggers heartbeat-specific prompt
- Agent updates MEMORY and DIARY after each tick

## Next Steps

### 5. TBD
- Evaluate real-world usage patterns and identify gaps
- Consider multi-agent coordination
- Explore richer tool registration beyond Pi built-ins
