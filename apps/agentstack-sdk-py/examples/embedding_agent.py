# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions import (
    EmbeddingDemand,
    EmbeddingServiceExtensionParams,
    EmbeddingServiceExtensionServer,
    EmbeddingServiceExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def embedding_demands_agent(
    input: Message,
    embedding: Annotated[
        EmbeddingServiceExtensionServer,
        EmbeddingServiceExtensionSpec(
            params=EmbeddingServiceExtensionParams(
                embedding_demands={
                    "fast": EmbeddingDemand(suggested=("openai/text-embedding-3-small",)),
                    "smart": EmbeddingDemand(suggested=("openai/text-embedding-3-large",)),
                }
            )
        ),
    ],
):
    """Agent that uses Embedding inference to respond to user input"""

    if embedding and embedding.data and embedding.data.embedding_fulfillments:
        smart_embedding = embedding.data.embedding_fulfillments.get("smart")
        fast_embedding = embedding.data.embedding_fulfillments.get("fast")

        if fast_embedding and hasattr(fast_embedding, "api_model"):
            api_model = fast_embedding.api_model
            yield AgentMessage(text=f"Fast Embedding access configured for model: {api_model}\n")

        if smart_embedding and hasattr(smart_embedding, "api_model"):
            api_model = smart_embedding.api_model
            yield AgentMessage(text=f"Smart Embedding access configured for model: {api_model}\n")
    else:
        yield AgentMessage(text="Embedding service not available")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
