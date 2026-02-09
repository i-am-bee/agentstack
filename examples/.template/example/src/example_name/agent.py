# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import Message
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def example_name_example(input: Message, context: RunContext):
    pass  # Implementation goes here


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    run()