# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions import (
    Citation,
    CitationExtensionServer,
    CitationExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.store.platform_context_store import PlatformContextStore

server = Server()


@server.agent(
    name="Citations example agent",
)
async def example_agent(
    input: Message,
    context: RunContext,
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],
):
    """Agent that demonstrates citation extension usage"""

    # Store the current message in the context store
    await context.store(input)

    # Simulate researching multiple sources
    research_text = """Based on recent research, artificial intelligence has made significant progress in natural
language processing. Studies show that transformer models have revolutionized the field, and
recent developments in large language models demonstrate remarkable capabilities in understanding
and generating human-like text."""

    # Create citations for the sources
    citations = [
        Citation(
            url="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            description="transformer models",
            start_index=research_text.index("transformer models"),
            end_index=research_text.index("transformer models") + len("transformer models"),
        ),
        Citation(
            url="https://openai.com/research/gpt-4",
            title="GPT-4 Technical Report",
            description="large language models",
            start_index=research_text.index("large language models"),
            end_index=research_text.index("large language models") + len("large language models"),
        ),
    ]

    # Send message with citation metadata
    message = AgentMessage(
        text=research_text,
        metadata=citation.citation_metadata(citations=citations),
    )
    yield message
    await context.store(message)


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), context_store=PlatformContextStore()
    )


if __name__ == "__main__":
    run()
