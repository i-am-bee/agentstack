# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Literal

import pydantic

from beeai_sdk.platform.client import PlatformClient, get_platform_client
from beeai_sdk.platform.types import Metadata


class ContextToken(pydantic.BaseModel):
    token: pydantic.Secret[str]
    expires_at: pydantic.AwareDatetime | None = None


class ResourceIdPermission(pydantic.BaseModel):
    id: str


class ContextPermissions(pydantic.BaseModel):
    files: set[Literal["read", "write", "extract", "*"]] = set()
    vector_stores: set[Literal["read", "write", "extract", "*"]] = set()


class Permissions(ContextPermissions):
    llm: set[Literal["*"] | ResourceIdPermission] = set()
    embeddings: set[Literal["*"] | ResourceIdPermission] = set()
    a2a_proxy: set[Literal["*"]] = set()
    providers: set[Literal["read", "write", "*"]] = set()  # write includes "show logs" permission
    variables: set[Literal["read", "write", "*"]] = set()
    contexts: set[Literal["read", "write", "*"]] = set()


class Context(pydantic.BaseModel):
    id: str
    created_at: pydantic.AwareDatetime
    updated_at: pydantic.AwareDatetime
    last_active_at: pydantic.AwareDatetime
    created_by: str
    metadata: Metadata | None = None

    @staticmethod
    async def create(
        *,
        metadata: Metadata | None = None,
        client: PlatformClient | None = None,
    ) -> Context:
        return pydantic.TypeAdapter(Context).validate_python(
            (await (client or get_platform_client()).post(url="/api/v1/contexts", json={"metadata": metadata}))
            .raise_for_status()
            .json()
        )

    async def get(
        self: Context | str,
        *,
        client: PlatformClient | None = None,
    ) -> Context:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        context_id = self if isinstance(self, str) else self.id
        return pydantic.TypeAdapter(Context).validate_python(
            (await (client or get_platform_client()).get(url=f"/api/v1/contexts/{context_id}"))
            .raise_for_status()
            .json()
        )

    async def delete(
        self: Context | str,
        *,
        client: PlatformClient | None = None,
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `File.delete("123")`
        context_id = self if isinstance(self, str) else self.id
        _ = (await (client or get_platform_client()).delete(url=f"/api/v1/contexts/{context_id}")).raise_for_status()

    async def generate_token(
        self: Context | str,
        *,
        client: PlatformClient | None = None,
        grant_global_permissions: Permissions | None = None,
        grant_context_permissions: ContextPermissions | None = None,
    ) -> ContextToken:
        """
        Generate token for agent authentication

        @param grant_global_permissions: Global permissions granted by the token. Must be subset of the users permissions
        @param grant_context_permissions: Context permissions granted by the token. Must be subset of the users permissions
        """
        # `self` has a weird type so that you can call both `instance.content()` to get content of an instance, or `File.content("123")`
        context_id = self if isinstance(self, str) else self.id
        grant_global_permissions = grant_global_permissions or Permissions()
        grant_context_permissions = grant_context_permissions or Permissions()
        return pydantic.TypeAdapter(ContextToken).validate_python(
            (
                await (client or get_platform_client()).post(
                    url=f"/api/v1/contexts/{context_id}/token",
                    json={
                        "grant_global_permissions": grant_global_permissions.model_dump(mode="json"),
                        "grant_context_permissions": grant_context_permissions.model_dump(mode="json"),
                    },
                )
            )
            .raise_for_status()
            .json()
        )
