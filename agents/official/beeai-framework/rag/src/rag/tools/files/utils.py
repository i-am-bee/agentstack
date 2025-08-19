# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
from contextlib import suppress

import pydantic.type_adapter
from a2a.types import FilePart, FileWithUri, Message, Role
from beeai_framework.backend import AssistantMessage, UserMessage

from beeai_sdk.platform import File
from beeai_sdk.util.file import PlatformFileUrl

FrameworkMessage = UserMessage | AssistantMessage


def to_framework_message(message: Message) -> FrameworkMessage:
    message_text = "".join(part.root.text for part in message.parts if part.root.kind == "text")

    if message.role == Role.agent:
        return AssistantMessage(message_text)

    if message.role == Role.user:
        return UserMessage(message_text)

    raise ValueError(f"Invalid message role: {message.role}")


async def extract_files(history: list[Message], incoming_message: Message) -> list[File]:
    """
    Extracts file URLs from the chat history and the current turn's messages.

    Args:
        context (Context): The current context of the chat session.
        incoming_message (Message): The message from the current turn.

    Returns:
        list[FileInfo]: A list of FileInfo objects containing file details.
    """
    # 1. Combine historical messages with the current turn
    all_messages = [*history, incoming_message]

    # 2. Flatten to all parts
    all_parts = (part.root for message in all_messages for part in message.parts)

    # 3. Collect, validate, deduplicate while preserving order
    seen: set[str] = set()
    file_ids: list[str] = []

    for part in all_parts:
        match part:
            case FilePart(file=FileWithUri(uri=uri)):
                with suppress(ValueError):
                    url = pydantic.type_adapter.TypeAdapter(PlatformFileUrl).validate_python(uri)
                    if url.file_id not in seen:
                        seen.add(url.file_id)
                        file_ids.append(url.file_id)

    # TODO: N+1 query issue, add bulk endpoint
    return await asyncio.gather(*(File.get(file_id) for file_id in seen))


def format_size(size: int | None) -> str:
    if size is None:
        return "unknown size"
    elif size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
