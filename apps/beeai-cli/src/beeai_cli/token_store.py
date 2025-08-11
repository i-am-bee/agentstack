# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path

import aiofiles

TOKEN_FILE = Path.home() / ".beeai" / "token.json"


async def save_token(token: str):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(TOKEN_FILE, "w") as f:
        await f.write(json.dumps({"token": token}))
    os.chmod(TOKEN_FILE, 0o600)


async def load_token() -> str | None:
    if TOKEN_FILE.exists():
        async with aiofiles.open(TOKEN_FILE) as f:
            content = await f.read()
            try:
                return json.loads(content).get("token")
            except json.JSONDecodeError:
                return None
    return None


async def clear_token():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
