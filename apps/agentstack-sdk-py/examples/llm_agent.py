# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions import (
    LLMDemand,
    LLMServiceExtensionParams,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def llm_demands_agent(
    input: Message,
    llm: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec(
            params=LLMServiceExtensionParams(
                llm_demands={
                    "fast": LLMDemand(suggested=("openai/gpt-4o-mini",)),
                    "smart": LLMDemand(suggested=("openai/gpt-5",)),
                }
            )
        ),
    ],
):
    """Agent that uses LLM inference to respond to user input"""

    if llm and llm.data and llm.data.llm_fulfillments:
        smart_llm = llm.data.llm_fulfillments.get("smart")
        fast_llm = llm.data.llm_fulfillments.get("fast")

        if fast_llm and hasattr(fast_llm, "api_model"):
            api_model = fast_llm.api_model
            yield AgentMessage(text=f"Fast LLM access configured for model: {api_model}\n")

        if smart_llm and hasattr(smart_llm, "api_model"):
            api_model = smart_llm.api_model
            yield AgentMessage(text=f"Smart LLM access configured for model: {api_model}\n")
    else:
        yield AgentMessage(text="LLM service not available")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
