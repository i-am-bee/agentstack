# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import functools
import shutil
from asyncio import CancelledError
from contextlib import suppress
from datetime import datetime, UTC
from typing import TypeVar, Iterable

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
