# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import StrEnum

import pydantic

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.platform.common import PaginatedResult


class UserRole(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"


class ChangeRoleResponse(pydantic.BaseModel):
    user_id: str
    new_role: UserRole


class User(pydantic.BaseModel):
    id: str
    role: UserRole
    email: str
    created_at: pydantic.AwareDatetime
    role_updated_at: pydantic.AwareDatetime | None = None

    @staticmethod
    async def get(*, client: PlatformClient | None = None) -> User:
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(User).validate_python(
                (await client.get(url="/api/v1/user")).raise_for_status().json()
            )

    @staticmethod
    async def list(
        *,
        email: str | None = None,
        limit: int = 40,
        page_token: str | None = None,
        client: PlatformClient | None = None,
    ) -> PaginatedResult[User]:
        async with client or get_platform_client() as client:
            params: dict[str, int | str] = {"limit": limit}
            if email:
                params["email"] = email
            if page_token:
                params["page_token"] = page_token

            return pydantic.TypeAdapter(PaginatedResult[User]).validate_python(
                (await client.get(url="/api/v1/users", params=params)).raise_for_status().json()
            )

    @staticmethod
    async def set_role(
        user_id: str,
        new_role: UserRole,
        *,
        client: PlatformClient | None = None,
    ) -> ChangeRoleResponse:
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(ChangeRoleResponse).validate_python(
                (await client.put(url=f"/api/v1/users/{user_id}/role", json={"new_role": new_role}))
                .raise_for_status()
                .json()
            )
