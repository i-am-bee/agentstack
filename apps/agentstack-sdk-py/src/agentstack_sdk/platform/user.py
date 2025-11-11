# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Literal

import pydantic

from agentstack_sdk.platform.client import PlatformClient, get_platform_client


class User(pydantic.BaseModel):
    id: str
    role: Literal["admin", "developer", "user"]
    email: pydantic.EmailStr
    created_at: pydantic.AwareDatetime

    @staticmethod
    async def get(*, client: PlatformClient | None = None) -> User:
        """Get the current user information."""
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(User).validate_python(
                (await client.get(url="/api/v1/user")).raise_for_status().json()
            )
