# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import concurrent.futures
import functools
from asyncio import CancelledError
from collections.abc import (
    Callable,
    Coroutine,
    Iterable,
)
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, cast, overload


def filter_dict[T](d: dict):
    return {k: v for k, v in d.items() if v is not None}


@overload
def filter_json_recursively(
    obj: dict[str, Any],
    values_to_exclude: Iterable[Any] | None = None,
    keys_to_exclude: Iterable[str] | None = None,
    exclude_empty: bool = False,
) -> dict[str, Any]: ...


@overload
def filter_json_recursively(
    obj: list[Any],
    values_to_exclude: Iterable[Any] | None = None,
    keys_to_exclude: Iterable[str] | None = None,
    exclude_empty: bool = False,
) -> list[Any]: ...


@overload
def filter_json_recursively[T](
    obj: T,
    values_to_exclude: Iterable[Any] | None = None,
    keys_to_exclude: Iterable[str] | None = None,
    exclude_empty: bool = False,
) -> T: ...


def filter_json_recursively(obj, values_to_exclude=None, keys_to_exclude=None, exclude_empty=False):
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
        return result

    elif isinstance(obj, list):
        list_res = [
            filter_json_recursively(item, values_to_exclude, keys_to_exclude, exclude_empty=exclude_empty)
            for item in obj
        ]
        if exclude_empty:
            list_res = [item for item in list_res if not isinstance(item, (list, dict)) or item]
        return list_res

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


def async_to_sync_isolated[**P, R](fn: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, R]:
    @functools.wraps(fn)
    def wrapped_fn(*args: P.args, **kwargs: P.kwargs) -> R:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(fn(*args, **kwargs)))
            return future.result()

    return wrapped_fn
