# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.extensions import LLMServiceExtensionServer, LLMServiceExtensionSpec
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def llm_access_example(
    input: Message,
    llm: Annotated[
        LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand(suggested=("ibm/granite-3-3-8b-instruct",))
    ],
):
    """Agent that uses LLM inference to respond to user input"""

    if llm and llm.data and llm.data.llm_fulfillments:
        # Extract the user's message
        user_message = get_message_text(input)

        # Get LLM configuration
        # Single demand is resolved to default (unless specified otherwise)
        llm_config = llm.data.llm_fulfillments.get("default")

        if llm_config:
            # Use the LLM configuration with your preferred client
            # The platform provides OpenAI-compatible endpoints
            api_model = llm_config.api_model
            api_key = llm_config.api_key
            api_base = llm_config.api_base

            yield AgentMessage(text=f"LLM access configured for model: {api_model}")
        else:
            yield AgentMessage(text="LLM configuration not found.")
    else:
        yield AgentMessage(text="LLM service not available.")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
