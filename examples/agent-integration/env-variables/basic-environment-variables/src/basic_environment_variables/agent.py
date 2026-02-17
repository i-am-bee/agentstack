# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import Message
from agentstack_sdk.a2a.extensions import AgentDetail
from agentstack_sdk.a2a.extensions.ui.agent_detail import EnvVar
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent(
    detail=AgentDetail(
        interaction_mode="multi-turn",
        variables=[
            EnvVar(name="THINKING_ENABLED", description="Whether to enable thinking mode for all users", required=True)
        ],
    )
)
async def basic_environment_variables_example(input: Message, context: RunContext):
    """Agent that uses environment variables for configuration"""
    thinking_enabled = os.getenv("THINKING_ENABLED", "false").lower() == "true"

    if thinking_enabled:
        yield "Thinking mode is enabled. I'll show my reasoning process."
    else:
        yield "Thinking mode is disabled. I'll provide direct responses."


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
