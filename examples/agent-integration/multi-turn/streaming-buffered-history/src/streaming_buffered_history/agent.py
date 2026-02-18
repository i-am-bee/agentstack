# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import os

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

server = Server()


async def example_tool() -> str:
    await asyncio.sleep(.1)  # doing some agent work
    return "tool result"


async def history_counter(history: list[Message]) -> str:
    """Create a concise conversation-state summary."""
    await asyncio.sleep(.1)  # doing some agent work
    user_count = sum(1 for item in history if item.role.value == "user")
    agent_count = sum(1 for item in history if item.role.value == "agent")
    history_count = len(history)
    return f"total={history_count}, user={user_count}, agent={agent_count}"


@server.agent()
async def streaming_buffered_history_example(input: Message, context: RunContext):
    """Stream partial chunks, execute framework tools, and persist one finalized assistant message."""
    # Store the user input as the first persisted item for this turn.
    await context.store(data=input)

    history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]

    current_message = get_message_text(input)

    # Stream user-facing partial output as each tool completes.
    buffered_parts: list[str] = []
    try: 
        part_1 = f"Received input: '{current_message}'"
        buffered_parts.append(part_1)
        yield AgentMessage(text=part_1)

        tool_result = await example_tool()
        part_2 = f"Tool call completed with result: '{tool_result}'"
        buffered_parts.append(part_2)
        yield AgentMessage(text=part_2)

        if len(history) > 3:
            raise ValueError("History is too long!")

        history_summary = await history_counter(history)
        history_part = f"History message counts including last user message, not including any of the current agent output: {history_summary}"
        buffered_parts.append(history_part)
        yield AgentMessage(text=history_part)

    except Exception as e:
        error_part = f"Error during execution: {e!s}"
        buffered_parts.append(error_part)
        yield AgentMessage(text=error_part)
    finally:
        # IMPORTANT: Persist only once after streaming finishes.
        #
        # Why not store each chunk?
        # - PlatformContextStore writes every `context.store()` call as a history item.
        # - Storing per chunk would fragment one assistant turn into many partial messages.
        # - A single aggregated write keeps replay, memory, and history semantics clean.
        aggregated_response = AgentMessage(text="\n".join(buffered_parts))
        await context.store(data=aggregated_response)


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        context_store=PlatformContextStore(),
    )


if __name__ == "__main__":
    run()
