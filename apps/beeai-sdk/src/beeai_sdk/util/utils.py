# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
import re
from collections.abc import AsyncIterator
from typing import Any, TypeVar

import httpx
from httpx import HTTPStatusError

V = TypeVar("V")


def filter_dict(map: dict[str, V], value_to_exclude: V = None) -> dict[str, V]:
    """Remove entries with unwanted values (None by default) from dictionary."""
    return {filter: value for filter, value in map.items() if value is not value_to_exclude}


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
            yield json.loads(re.sub("^data:", "", line).strip())
