# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message

from beeai_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from beeai_sdk.a2a.types import AgentMessage
from beeai_sdk.server import Server

server = Server()


@server.agent()
async def llm_demands_agent(
    input: Message,
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand(suggested=("openai/gpt-4o-mini",))],
):
    """Agent that uses LLM inference to respond to user input"""

    if llm and llm.data and llm.data.llm_fulfillments:
        llm_config = llm.data.llm_fulfillments.get("default")
        if llm_config and hasattr(llm_config, "api_model"):
            api_model = llm_config.api_model
            yield AgentMessage(text=f"LLM access configured for model: {api_model}")
        else:
            yield AgentMessage(text="LLM configuration not found or invalid")
    else:
        yield AgentMessage(text="LLM service not available")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
