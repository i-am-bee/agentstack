# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from functools import cache

import httpx


@cache
def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="http://127.0.0.1:8333")
