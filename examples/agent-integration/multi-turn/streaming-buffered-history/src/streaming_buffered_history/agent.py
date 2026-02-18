# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

server = Server()


def chunk_text(text: str, chunk_size: int = 20) -> list[str]:
    """Split text into deterministic chunks to simulate token-by-token streaming."""
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


@server.agent()
async def streaming_buffered_history_example(input: Message, context: RunContext):
    """Stream partial chunks while persisting a single finalized assistant message."""
    # Store the user input as the first persisted item for this turn.
    await context.store(input)

    history = [message async for message in context.load_history() if isinstance(message, Message) and message.parts]

    current_message = get_message_text(input)
    final_response_text = (
        "Streaming response complete. "
        f"Current message was: '{current_message}'. "
        f"Persisted history now contains {len(history)} message(s), including this user input."
    )

    # Stream chunks immediately so users see incremental output in real time.
    buffered_chunks: list[str] = []
    for chunk in chunk_text(final_response_text):
        buffered_chunks.append(chunk)
        yield AgentMessage(text=chunk)

    # IMPORTANT: Persist only once after streaming finishes.
    #
    # Why not store each chunk?
    # - PlatformContextStore writes every `context.store()` call as a history item.
    # - Storing per chunk would fragment one assistant turn into many partial messages.
    # - A single aggregated write keeps replay, memory, and history semantics clean.
    aggregated_response = AgentMessage(text="".join(buffered_chunks))
    await context.store(aggregated_response)


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        context_store=PlatformContextStore(),
    )


if __name__ == "__main__":
    run()
