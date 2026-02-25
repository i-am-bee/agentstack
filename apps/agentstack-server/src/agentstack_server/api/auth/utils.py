# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from functools import reduce
from typing import Any

from starlette.datastructures import URL


def create_resource_uri(url: URL) -> str:
    return f"{url.scheme}://{url.netloc}{url.path}".rstrip("/")


def get_claims_by_path(claims: dict[str, Any], path: str) -> Any:
    return reduce(
        lambda d, key: d.get(key, {}) if isinstance(d, dict) else {},
        path.split("."),
        claims,
    )
