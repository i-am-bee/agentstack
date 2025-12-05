# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import concurrent.futures
import functools
import json
import re
from asyncio import CancelledError
from collections.abc import AsyncIterable, Callable, Iterable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, cast

from agentstack_server.types import JsonValue


def filter_dict[T, V](map: dict[str, T | V], value_to_exclude: V = None) -> dict[str, T]:
    """Remove entries with unwanted values (None by default) from dictionary."""
    return {key: cast(T, value) for key, value in map.items() if value is not value_to_exclude}


def filter_json_recursively[T: JsonValue](
    obj: T,
    values_to_exclude: Iterable[Any] | None = None,
    keys_to_exclude: Iterable[str] | None = None,
    exclude_empty: bool = False,
) -> T:
    keys_to_exclude = set(keys_to_exclude) if keys_to_exclude else set()
    values_to_exclude = set(values_to_exclude) if values_to_exclude else set()
    if isinstance(obj, dict):
        result = {
            key: filter_json_recursively(value, values_to_exclude, keys_to_exclude, exclude_empty=exclude_empty)
            for key, value in obj.items()
            if key not in keys_to_exclude and (isinstance(value, (list, dict)) or value not in values_to_exclude)
        }
        if exclude_empty:
            result = {key: value for key, value in result.items() if not isinstance(value, (list, dict)) or value}
        return result  # pyright: ignore[reportReturnType]

    elif isinstance(obj, list):
        list_res = [
            filter_json_recursively(item, values_to_exclude, keys_to_exclude, exclude_empty=exclude_empty)
            for item in obj
        ]
        if exclude_empty:
            list_res = [item for item in list_res if not isinstance(item, (list, dict)) or item]
        return list_res  # pyright: ignore[reportReturnType]

    return obj


def pick[DictType: dict[str, Any]](dict: DictType, keys: Iterable[str]) -> DictType:
    return cast(DictType, {key: value for key, value in dict.items() if key in keys})


def omit[DictType: dict[str, Any]](dict: DictType, keys: Iterable[str]) -> DictType:
    return cast(DictType, {key: value for key, value in dict.items() if key not in keys})


def extract_messages(exc: BaseException) -> list[tuple[str, str]]:
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


async def cancel_task(task: asyncio.Task[None] | None):
    if task:
        task.cancel()
        with suppress(CancelledError):
            await task


def utc_now() -> datetime:
    return datetime.now(UTC)


def async_to_sync_isolated[AnyCallableT: Callable[..., Any]](fn: AnyCallableT) -> AnyCallableT:
    @functools.wraps(fn)
    def wrapped_fn(*args, **kwargs):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(fn(*args, **kwargs)))
            return future.result()

    return wrapped_fn


async def extract_string_value_stream(
    async_stream: Callable[[int], AsyncIterable[str]], key: str, chunk_size: int = 1024
) -> AsyncIterable[str]:
    buffer = ""
    max_buffer_size = len(key) * 2
    state = "outside"
    if chunk_size < max_buffer_size:
        raise ValueError("Chunk size too small")

    async for chunk in async_stream(chunk_size):
        buffer += chunk
        if state == "outside":
            if match := re.search(rf'"{key}" *: *"', buffer):
                buffer = buffer[match.end() :]
                state = "inside"
            else:
                buffer = buffer[-max_buffer_size:]
        if state == "inside":
            backslash_count = 0
            for idx, char in enumerate(buffer):
                if char == "\\":
                    backslash_count += 1
                elif char == '"':
                    if backslash_count % 2 == 0:
                        yield json.loads(f'"{buffer[:idx]}"')
                        return
                    backslash_count = 0
                else:
                    backslash_count = 0
            if backslash_count % 2 == 0:
                yield json.loads(f'"{buffer}"')
                buffer = ""
            else:
                yield json.loads(f'"{buffer[:-1]}"')
                buffer = "\\"

    if state == "inside":
        raise EOFError("Unterminated string value in JSON input")
    else:
        raise KeyError(f"Key {key} not found in JSON input")
