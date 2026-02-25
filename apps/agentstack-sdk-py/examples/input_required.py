# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncGenerator

from a2a.types import Message, TaskStatus

from agentstack_sdk.a2a.types import InputRequired
from agentstack_sdk.server import Server

server = Server()


def get_text(part) -> str:
    """Safely extract 'text' from a FilePart or DataPart"""
    return getattr(part.root, "text", "")


@server.agent()
async def input_required(
    message: Message,
) -> AsyncGenerator[TaskStatus | str, Message]:
    """Agent that asks for user input during execution"""

    yield "I'm processing your request...\n"

    # Ask for email
    response = yield InputRequired(text="What email address should I use?")
    email = get_text(response.parts[0])
    yield f"Great! I'll use {email}\n"

    try:
        # Ask for subject line
        response = yield InputRequired(text="What subject line do you want?")
        subject = get_text(response.parts[0])
        yield f"Perfect! Sending email to {email} with subject: {subject}"
    except Exception:
        yield "No email :("


def run():
    server.run()


if __name__ == "__main__":
    run()
