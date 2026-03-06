# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from agentstack_sdk.types import JsonValue
from agentstack_sdk.a2a.types import Metadata
from a2a.types import Message
import asyncio
from asyncio import CancelledError
from contextlib import suppress

from a2a.server.events import QueueManager


async def cancel_task(task: asyncio.Task):
    task.cancel()
    with suppress(CancelledError):
        await task


async def close_queue(queue_manager: QueueManager, queue_name: str, immediate: bool = False):
    """Closes a queue without blocking the QueueManager

    By default, QueueManager.close() will block all QueueManager operations (creating new queues, etc)
    until all queue events are processed. This can have unexpected side effects, we avoid this by closing queue
    independently and then removing it from queue_manager
    """
    if queue := await queue_manager.get(queue_name):
        await queue.close(immediate=immediate)
        await queue_manager.close(queue_name)


def _merge_recursive(obj: JsonValue, other: JsonValue) -> JsonValue:
    if isinstance(obj, dict) and isinstance(other, dict):
        merged = {**obj}
        for k, v in other.items():
            if k in merged:
                merged[k] = _merge_recursive(merged[k], v)
            else:
                merged[k] = v
        return merged
    elif isinstance(obj, list) and isinstance(other, list):
        return obj + other
    else:
        return other


def merge_metadata(*metadata_items: Metadata) -> Metadata:
    result = Metadata()
    for m in metadata_items:
        for k, v in m.items():
            result[k] = _merge_recursive(result.get(k, {}), v)
    return result


def merge_messages(*messages: Message) -> Message | None:
    if not messages:
        return None
    merged = Message()
    merged.CopyFrom(messages[0])
    for msg in messages[1:]:
        merged.parts.extend(msg.parts)
        for k, v in msg.metadata.items():
            merged.metadata[k] = v
    return merged
