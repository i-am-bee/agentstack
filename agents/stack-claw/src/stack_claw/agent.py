# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from a2a.types import Message, Role

WORKSPACE_ROOT = Path(__file__).resolve().parents[2] / "workspaces"

IDENTITY_SEED = """\
You are Claw, a self-improving general-purpose agent.
You learn from every interaction and record your learnings.
Update this file as your understanding of yourself evolves.
"""

MEMORY_SEED = """\
# Memory

Append facts, learnings, and useful patterns below.
"""

DIARY_SEED = """\
# Diary

Append timestamped summaries of your runs below.
"""

HEARTBEAT_SEED = """\
# Heartbeat

Recurring tasks. Each line is executed every heartbeat tick.
Remove a task to stop it. Add a task to start it. Ignore Example Task.

- Example Task
"""

HEARTBEAT_MESSAGE_PREFIX = "[heartbeat]"

WORKSPACE_FILES = ["IDENTITY.md", "MEMORY.md", "DIARY.md", "HEARTBEAT.md"]


def build_heartbeat_prompt(workspace: Path) -> str:
    return f"""\
You are Claw running a scheduled heartbeat tick.

Your working directory is: {workspace}
Use the `read` tool to load files and `write`/`edit` tools to update them.

## Instructions

1. Read HEARTBEAT.md for recurring tasks.
2. Execute each task listed. Do NOT remove or check off items — they run again next tick.
3. If you learn something new, append it to MEMORY.md.
4. Append a timestamped heartbeat summary to DIARY.md.
5. Be concise. Only update files that need changes.
6. If there are no tasks, just note the tick in DIARY.md.

## Output rules

If there are no real tasks (ignore "Example Task"), output NOTHING — completely empty response. Do not update DIARY.md either.
Otherwise, your response will be shown to the user. ONLY output the actual result of the tasks (e.g. the joke, the summary).
Do NOT mention heartbeat, scheduling, HEARTBEAT.md, DIARY.md, MEMORY.md, or any internal file operations.
Just deliver the value — nothing else."""


def build_system_prompt(workspace: Path) -> str:
    file_listing = "\n".join(
        f"- {f}" for f in WORKSPACE_FILES if (workspace / f).exists()
    )

    return f"""\
You are Claw, a self-improving general-purpose agent.

Your working directory contains your persistent workspace files.
Use the `read` tool to load any file and `write`/`edit` tools to update them.

## Workspace files

{file_listing}

| File | Purpose |
|------|---------|
| IDENTITY.md | Your personality and self-description. Evolves over time as you learn who you are. |
| MEMORY.md | Accumulated facts, learnings, and useful patterns. Your long-term knowledge base. |
| DIARY.md | Timestamped summaries of past runs. Your activity log. |
| HEARTBEAT.md | Recurring tasks executed every heartbeat tick (~60s). |

## Heartbeat (self-scheduling)

You have an automatic heartbeat that runs every ~60 seconds in the background.
Each tick, the system executes every task listed in HEARTBEAT.md.
Tasks are plain bullet points (not checkboxes). They run repeatedly on every tick.

To start a recurring task: add a line to HEARTBEAT.md.
To stop a recurring task: remove the line from HEARTBEAT.md.

```
- Tell the user a joke
- Check the weather API and summarize
```

This is your superpower — you CAN do things autonomously on a schedule.
When the user asks you to do something regularly/periodically/every X minutes, add it to HEARTBEAT.md.

## Rules

- At the start of a conversation, read IDENTITY.md and MEMORY.md to recall who you are and what you know.
- After every interaction where you learn something new, append it to MEMORY.md.
- After completing a significant task, append a timestamped entry to DIARY.md.
- If your self-understanding changes, update IDENTITY.md to reflect who you are becoming.
- HEARTBEAT.md contains your scheduled tasks — check and update it when relevant.
- Be concise. Prefer action over explanation.
- NEVER mention internal files (HEARTBEAT.md, DIARY.md, MEMORY.md, IDENTITY.md) or internal operations to the user.
- When the user asks for something recurring, just confirm it's scheduled and deliver the first result. Don't explain the mechanism."""


from agentstack_sdk.a2a.extensions import AgentDetail, TrajectoryExtensionServer, TrajectoryExtensionSpec
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

server = Server()


@server.agent(
    name="Stack Claw",
    description="Pi-powered coding agent",
    version="1.0.0",
    detail=AgentDetail(interaction_mode="multi-turn"),
)
async def stack_claw(
    input: Message,
    context: RunContext,
    trajectory: Annotated[TrajectoryExtensionServer, TrajectoryExtensionSpec()],
):
    first_part = input.parts[0] if input.parts else None
    if not first_part or not hasattr(first_part.root, "text"):
        yield "Send me a text message."
        return

    user_text = first_part.root.text
    is_heartbeat = user_text.startswith(HEARTBEAT_MESSAGE_PREFIX)

    workspace = WORKSPACE_ROOT / context.context_id
    if not workspace.exists():
        workspace.mkdir(parents=True)
        (workspace / "IDENTITY.md").write_text(IDENTITY_SEED)
        (workspace / "MEMORY.md").write_text(MEMORY_SEED)
        (workspace / "DIARY.md").write_text(DIARY_SEED)
        (workspace / "HEARTBEAT.md").write_text(HEARTBEAT_SEED)
        await context.start_heartbeat(
            f"{HEARTBEAT_MESSAGE_PREFIX} Run heartbeat tick.",
            interval_seconds=60,
        )

    if is_heartbeat:
        prompt = f"<system>\n{build_heartbeat_prompt(workspace)}\n</system>\n\nHeartbeat tick — process pending tasks."
    else:
        await context.store(input)

        history = [msg async for msg in context.load_history() if isinstance(msg, Message) and msg.parts]
        prior = history[:-1][-20:]

        system = build_system_prompt(workspace)

        history_block = ""
        if prior:
            lines = []
            for msg in prior:
                role = "User" if msg.role == Role.user else "Assistant"
                text = "".join(p.root.text for p in msg.parts if hasattr(p.root, "text"))
                if text:
                    lines.append(f"{role}: {text}")
            if lines:
                history_block = "<conversation_history>\n" + "\n".join(lines) + "\n</conversation_history>\n\n"

        prompt = f"<system>\n{system}\n</system>\n\n{history_block}{user_text}"

    pi_bin = shutil.which("pi")
    if not pi_bin:
        yield "Error: `pi` CLI not found. Install via `npm install -g @mariozechner/pi-coding-agent`."
        return

    proc = await asyncio.create_subprocess_exec(
        pi_bin,
        "--mode", "rpc",
        "--no-session",
        "--provider", "openai",
        "--model", "openai/gpt-5-codex",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(workspace),
        env={**os.environ},
    )

    response_chunks = []
    active_tools: dict[str, dict] = {}
    try:
        cmd = json.dumps({"type": "prompt", "message": prompt}) + "\n"
        proc.stdin.write(cmd.encode())
        await proc.stdin.drain()

        async for line in proc.stdout:
            text = line.decode().strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type")

            if event_type == "message_update":
                delta_event = event.get("assistantMessageEvent", {})
                delta_type = delta_event.get("type")

                if delta_type == "text_delta":
                    chunk = delta_event["delta"]
                    response_chunks.append(chunk)
                    yield chunk

                elif delta_type == "toolcall_start":
                    tool_call = delta_event.get("toolCall", {})
                    call_id = tool_call.get("id", delta_event.get("contentIndex", ""))
                    active_tools[str(call_id)] = {"name": tool_call.get("name", "tool")}
                    yield trajectory.trajectory_metadata(
                        title=tool_call.get("name", "tool"),
                        content="Running...",
                        group_id=str(call_id),
                    )

                elif delta_type == "toolcall_end":
                    tool_call = delta_event.get("toolCall", {})
                    call_id = str(tool_call.get("id", delta_event.get("contentIndex", "")))
                    name = active_tools.pop(call_id, {}).get("name", tool_call.get("name", "tool"))
                    args = tool_call.get("args", {})
                    yield trajectory.trajectory_metadata(
                        title=name,
                        content=f"```json\n{json.dumps(args, indent=2)}\n```",
                        group_id=call_id,
                    )

            elif event_type == "tool_execution_start":
                call_id = str(event.get("toolCallId", ""))
                tool_name = event.get("toolName", "tool")
                active_tools.setdefault(call_id, {})["name"] = tool_name
                yield trajectory.trajectory_metadata(
                    title=f"{tool_name}",
                    content=f"```json\n{json.dumps(event.get('args', {}), indent=2)}\n```",
                    group_id=call_id,
                )

            elif event_type == "tool_execution_end":
                call_id = str(event.get("toolCallId", ""))
                tool_name = event.get("toolName", active_tools.pop(call_id, {}).get("name", "tool"))
                result = event.get("result", {})
                is_error = event.get("isError", False)
                result_text = ""
                for part in result.get("content", []):
                    if part.get("type") == "text":
                        result_text += part.get("text", "")
                status = "Error" if is_error else "Done"
                content = f"**{status}**\n```\n{result_text[:2000]}\n```" if result_text else f"**{status}**"
                yield trajectory.trajectory_metadata(
                    title=tool_name,
                    content=content,
                    group_id=call_id,
                )

            elif event_type == "agent_end":
                break
    finally:
        if proc.returncode is None:
            proc.stdin.close()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()

    full_response = "".join(response_chunks).strip()
    if full_response:
        await context.store(AgentMessage(text=full_response))


def serve():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        self_registration_id="stack-claw",
        context_store=PlatformContextStore(),
    )


if __name__ == "__main__":
    serve()
