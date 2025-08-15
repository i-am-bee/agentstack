# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import httpx
from pydantic import AnyUrl


async def read_file(
    file_url: AnyUrl,
) -> tuple[str, str]:
    print(f"Reading file from {file_url}...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(str(file_url))
        content_type = resp.headers.get("Content-Type")
        return (resp.content.decode(), content_type)
