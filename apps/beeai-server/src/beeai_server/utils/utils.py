# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import concurrent.futures
import functools
import shutil
from asyncio import CancelledError
from contextlib import suppress
from datetime import datetime, UTC
from typing import TypeVar, Iterable, Callable, Any

import anyio.to_thread

T = TypeVar("T")
V = TypeVar("V")
DictType = TypeVar("DictType", bound=dict)


def filter_dict(map: dict[str, T | V], value_to_exclude: V = None) -> dict[str, V]:
    """Remove entries with unwanted values (None by default) from dictionary."""
    return {filter: value for filter, value in map.items() if value is not value_to_exclude}


def pick(dict: DictType, keys: Iterable[str]) -> DictType:
    return {key: value for key, value in dict.items() if key in keys}


def omit(dict: DictType, keys: Iterable[str]) -> DictType:
    return {key: value for key, value in dict.items() if key not in keys}


def extract_messages(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


@functools.cache
def _which_sync(command: str):
    return shutil.which(command)


async def which(command: str):
    return await anyio.to_thread.run_sync(_which_sync, command)


async def cancel_task(task: asyncio.Task[None] | None):
    if task:
        task.cancel()
        with suppress(CancelledError):
            await task


def utc_now() -> datetime:
    return datetime.now(UTC)


AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])


def async_to_sync_isolated(fn: AnyCallableT) -> AnyCallableT:
    @functools.wraps(fn)
    def wrapped_fn(*args, **kwargs):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(fn(*args, **kwargs)))
            return future.result()

    return wrapped_fn
