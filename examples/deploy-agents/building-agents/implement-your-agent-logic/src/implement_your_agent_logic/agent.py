# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def implement_your_agent_logic_example(input: Message, context: RunContext):
    """Polite agent that greets the user"""
    hello_template: str = os.getenv("HELLO_TEMPLATE", "Ciao %s!")
    yield AgentMessage(text=hello_template % get_message_text(input))


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
