# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator

from a2a.client import create_text_message_object
from a2a.types import Message, TaskState, TaskStatus

from beeai_sdk.server import Server

server = Server()


@server.agent()
async def awaiter_agent(message: Message) -> AsyncGenerator[TaskStatus | Message | str, Message]:
    """Awaits a user message"""
    yield f"got initial message: {message.parts[0].root.text}\n"
    yield "second message\n"
    message = yield TaskStatus(
        message=create_text_message_object(content="give me auth\n"), state=TaskState.auth_required
    )
    yield f"got follow up message {message.message_id}: {message.parts[0].root.text}"


if __name__ == "__main__":
    server.run(self_registration=False)
