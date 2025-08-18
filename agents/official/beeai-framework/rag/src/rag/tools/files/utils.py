# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import re
from typing import Iterable

from a2a.types import FilePart, FileWithUri, Message, Role
from beeai_framework.backend import AssistantMessage, UserMessage

from beeai_sdk.platform import File

FrameworkMessage = UserMessage | AssistantMessage


def to_framework_message(message: Message) -> FrameworkMessage:
    message_text = "".join(
        part.root.text for part in message.parts if part.root.kind == "text"
    )

    if message.role == Role.agent:
        return AssistantMessage(message_text)

    if message.role == Role.user:
        return UserMessage(message_text)

    raise ValueError(f"Invalid message role: {message.role}")


async def extract_files(
    history: list[Message],
    incoming_message: Message,
) -> list[File]:
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
    files: list[File] = []

    for part in all_parts:
        if not isinstance(part, FilePart):
            continue

        if not isinstance(part.file, FileWithUri):
            continue

        url = part.file.uri.replace(
            "{platform_url}", os.getenv("PLATFORM_URL", "127.0.0.1:8333")
        )
        # if url and url not in seen:
        #     fileInfo = await get_file_chat_info(
        #         url,
        #         content_type=part.file.mime_type or "application/octet-stream",
        #         existing_filenames=existing_filenames,
        #         origin_type=OriginType.UPLOADED,  # Default to uploaded since we can't access part.role
        #     )
        #     if fileInfo:
        #         files.append(fileInfo)
        #         existing_filenames.append(fileInfo.display_filename)
        #     seen.add(url)
        if url and url not in seen:
            file = await File.get(extract_file_id_from_url(url))
            if file:
                files.append(file)
            seen.add(url)

    return files

def format_size(size: int | None) -> str:
    if size is None:
        return "unknown size"
    elif size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def extract_file_id_from_url(url: str) -> str:
    """
    Extract file ID from platform file URL format.

    Expected format: http://{platform_url}/api/v1/files/{file_id}/content
    Args:
        url (str): The URL from which to extract the file ID.
    Raises:
        ValueError: If the file ID cannot be extracted from the URL

    Examples:
        >>> extract_file_id_from_url("http://localhost:8333/api/v1/files/51797992-1dab-4c4d-bdac-9e90c28bbef1/content")
        '51797992-1dab-4c4d-bdac-9e90c28bbef1'
    """
    file_id_match = re.search(r"/files/([^/]+)/content", url)
    if not file_id_match:
        raise ValueError(f"Could not extract file_id from URL: {url}")
    return file_id_match.group(1)
