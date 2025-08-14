# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator

from a2a.types import Message, TaskStatus

from beeai_sdk.a2a.types import AuthRequired
from beeai_sdk.server import Server

server = Server()


@server.agent()
async def awaiter_agent(message: Message) -> AsyncGenerator[TaskStatus | Message | str, Message]:
    """Awaits a user message"""
    yield f"got initial message: {message.parts[0].root.text}\n"
    yield "second message\n"

    message = yield AuthRequired(text="can I do this?")
    yield f"got follow up message {message.message_id}: {message.parts[0].root.text}"


if __name__ == "__main__":
    server.run(self_registration=False)
