# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

import httpx

from beeai_sdk.util import resource_context

get_client, with_client = resource_context(
    httpx.AsyncClient, lambda: httpx.AsyncClient(base_url=os.environ.get("PLATFORM_URL", "http://127.0.0.1:8333"))
)

__all__ = [
    "get_client",
    "with_client",
]
