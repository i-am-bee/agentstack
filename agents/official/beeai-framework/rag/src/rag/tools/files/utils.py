# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import re
from typing import Iterable

from a2a.types import FilePart, FileWithUri, Message, Role
from beeai_framework.backend import AssistantMessage, UserMessage

from rag.helpers.platform import get_file_info
from rag.tools.files.model import FileChatInfo, OriginType

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
) -> list[FileChatInfo]:
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
    files: list[FileChatInfo] = []
    existing_filenames: list[str] = []

    for part in all_parts:
        if not isinstance(part, FilePart):
            continue

        if not isinstance(part.file, FileWithUri):
            continue

        url = part.file.uri.replace(
            "{platform_url}", os.getenv("PLATFORM_URL", "127.0.0.1:8333")
        )
        if url and url not in seen:
            fileInfo = await get_file_chat_info(
                url,
                content_type=part.file.mimeType or "application/octet-stream",
                existing_filenames=existing_filenames,
                origin_type=OriginType.UPLOADED,  # Default to uploaded since we can't access part.role
            )
            if fileInfo:
                files.append(fileInfo)
                existing_filenames.append(fileInfo.display_filename)
            seen.add(url)

    return files


async def get_file_chat_info(
    url: str, content_type: str, origin_type: OriginType, existing_filenames: list[str]
) -> FileChatInfo:
    # 1. Extract the file-ID from the signed-download URL
    file_id_match = re.search(r"/([^/]+)/content", str(url))
    if not file_id_match:
        raise ValueError(f"Could not extract file_id from: {url!r}")
    file_id = file_id_match.group(1)

    # 2. Ask the platform for the file metadata
    file_response = await get_file_info(file_id)
    if not file_response:
        raise ValueError(f"File with ID {file_id} not found on the platform.")

    # 3. Merge the API data with the known url & content_type
    merged_payload = {
        **file_response.model_dump(),  # → id, filename, file_size_bytes …
        "url": url,  # override / add
        "content_type": content_type,
        "display_filename": next_unused_filename(
            file_response.filename, existing_filenames
        ),  # ensure unique display name
        "origin_type": origin_type,
    }

    # 4. Validate & coerce with Pydantic
    file_info = FileChatInfo.model_validate(merged_payload)

    # 5. Extra safeguard: make sure filename is a string
    if not isinstance(file_info.filename, str):
        file_info.filename = str(file_info.filename)

    return file_info


def next_unused_filename(name: str, existing: Iterable[str]) -> str:
    """Return a filename that is not present in *existing* by appending
    '(n)' before the extension when needed.

    Return *name* unchanged if it is not in *existing*.
    Otherwise append / increment a numeric suffix in parentheses
    just before the extension:  foo.txt  ->  foo(1).txt  ->  foo(2).txt …

    Parameters
    ----------
    name      : the desired file name, e.g. 'todo.txt'
    existing  : iterable of names already taken (case-sensitive)

    Examples
    --------
    >>> next_unused_filename("todo.txt", ["todo.txt", "todo(1).txt"])
    'todo(2).txt'
    """
    existing_set = set(existing)
    if name not in existing_set:  # fast path – no clash
        return name

    # split off the last extension (handles .tar.gz etc. by design choice)
    if "." in name:
        base, ext = name.rsplit(".", 1)
        ext = f".{ext}"
    else:
        base, ext = name, ""

    # regex to capture already-numbered siblings: foo(12).txt
    numbered = re.compile(rf"^{re.escape(base)}\((\d+)\){re.escape(ext)}$")

    # collect the numbers already used for this base
    used = {int(m.group(1)) for n in existing_set if (m := numbered.match(n))}

    # smallest positive integer that isn’t taken
    i = 1
    while i in used:
        i += 1

    return f"{base}({i}){ext}"


def format_size(size: int | None) -> str:
    if size is None:
        return "unknown size"
    elif size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
