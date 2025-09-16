# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import re
from contextlib import suppress
from typing import Iterable

import pydantic
from a2a.types import FilePart, FileWithUri, Message, Role
from beeai_framework.backend import AssistantMessage, UserMessage

from beeai_sdk.platform import File
from beeai_sdk.util.file import PlatformFileUrl
from chat.tools.files.model import FileChatInfo

FrameworkMessage = UserMessage | AssistantMessage


def to_framework_message(message: Message, all_attachments: list[FileChatInfo]) -> FrameworkMessage:
    message_text = "".join(part.root.text for part in message.parts if part.root.kind == "text")
    if attachments := [file for file in all_attachments if file.message_id == message.message_id]:
        message_text += "\nAttached files:\n" + "\n".join([file.description for file in attachments])

    match message.role:
        case Role.agent:
            return AssistantMessage(message_text)
        case Role.user:
            return UserMessage(message_text)
        case _:
            raise ValueError(f"Invalid message role: {message.role}")


async def extract_files(history: list[Message]) -> list[FileChatInfo]:
    """
    Extracts file URLs from the chat history and the current turn's messages.

    Args:
        context (Context): The current context of the chat session.

    Returns:
        list[FileChatInfo]: A list of FileInfo objects containing file details.
    """
    # 1. Collect, validate, deduplicate while preserving order
    seen: set[str] = set()
    files: dict[str, Message] = {}

    for item in history:
        for part in item.parts:
            match part.root:
                case FilePart(file=FileWithUri(uri=uri)):
                    with suppress(ValueError):
                        url = pydantic.type_adapter.TypeAdapter(PlatformFileUrl).validate_python(uri)
                        if url.file_id not in seen:
                            seen.add(url.file_id)
                            files[url.file_id] = item

    # TODO: N+1 query issue, add bulk endpoint
    file_objects = await asyncio.gather(*(File.get(file_id) for file_id in files))
    existing_filenames = set()
    result = []
    for file, message in zip(file_objects, files.values()):
        result.append(
            FileChatInfo(
                file=file,
                role=message.role,
                message_id=message.message_id,
                display_filename=next_unused_filename(file.filename, existing_filenames),
            )
        )
        existing_filenames.add(result[-1].display_filename)
    return result


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
