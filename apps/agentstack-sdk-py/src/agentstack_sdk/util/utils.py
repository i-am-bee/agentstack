# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, TypeVar

import httpx
from httpx import HTTPStatusError

T = TypeVar("T")


def filter_dict(d: dict):
    return {k: v for k, v in d.items() if v is not None}


async def parse_stream(response: httpx.Response) -> AsyncIterator[dict[str, Any]]:
    if response.is_error:
        error = ""
        try:
            [error] = [json.loads(message) async for message in response.aiter_text()]
            error = error.get("detail", str(error))
        except Exception:
            response.raise_for_status()
        raise HTTPStatusError(message=error, request=response.request, response=response)
    async for line in response.aiter_lines():
        if line:
            data = re.sub("^data:", "", line).strip()
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                yield {"event": data}


def extract_messages(exc: BaseException) -> list[tuple[str, str]]:
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        return [(type(exc).__name__, str(exc))]


def utc_now() -> datetime:
    return datetime.now(UTC)
