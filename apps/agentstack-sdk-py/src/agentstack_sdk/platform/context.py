# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal
from uuid import UUID

import pydantic
from a2a.types import Artifact, Message
from pydantic import AwareDatetime, BaseModel, SerializeAsAny

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.platform.common import PaginatedResult
from agentstack_sdk.platform.types import Metadata, MetadataPatch
from agentstack_sdk.util.utils import filter_dict


class ContextHistoryItem(BaseModel):
    id: UUID
    data: Artifact | Message
    created_at: AwareDatetime
    context_id: UUID
    kind: Literal["message", "artifact"]


class ContextToken(pydantic.BaseModel):
    context_id: str
    token: pydantic.Secret[str]
    expires_at: pydantic.AwareDatetime | None = None


class ResourceIdPermission(pydantic.BaseModel):
    id: str


class ContextPermissions(pydantic.BaseModel):
    files: set[Literal["read", "write", "extract", "*"]] = set()
    vector_stores: set[Literal["read", "write", "extract", "*"]] = set()
    context_data: set[Literal["read", "write", "*"]] = set()


class Permissions(ContextPermissions):
    llm: set[Literal["*"] | ResourceIdPermission] = set()
    embeddings: set[Literal["*"] | ResourceIdPermission] = set()
    a2a_proxy: set[Literal["*"]] = set()
    model_providers: set[Literal["read", "write", "*"]] = set()
    variables: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()

    providers: set[Literal["read", "write", "*"]] = set()  # write includes "show logs" permission
    provider_variables: set[Literal["read", "write", "*"]] = set()

    contexts: set[Literal["read", "write", "*"]] = set()
    mcp_providers: set[Literal["read", "write", "*"]] = set()
    mcp_tools: set[Literal["read", "*"]] = set()
    mcp_proxy: set[Literal["*"]] = set()


class Context(pydantic.BaseModel):
    id: str
    created_at: pydantic.AwareDatetime
    updated_at: pydantic.AwareDatetime
    last_active_at: pydantic.AwareDatetime
    created_by: str
    provider_id: str | None = None
    metadata: Metadata | None = None

    @staticmethod
    async def create(
        *,
        metadata: Metadata | None = None,
        provider_id: str | None = None,
        client: PlatformClient | None = None,
    ) -> Context:
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Context).validate_python(
                (
                    await client.post(
                        url="/api/v1/contexts",
                        json=filter_dict({"metadata": metadata, "provider_id": provider_id}),
                    )
                )
                .raise_for_status()
                .json()
            )

    @staticmethod
    async def list(
        *,
        client: PlatformClient | None = None,
        page_token: str | None = None,
        limit: int | None = None,
        order: Literal["asc"] | Literal["desc"] | None = None,
        order_by: Literal["created_at"] | Literal["updated_at"] | None = None,
        include_empty: bool = True,
        provider_id: str | None = None,
    ) -> PaginatedResult[Context]:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(PaginatedResult[Context]).validate_python(
                (
                    await client.get(
                        url="/api/v1/contexts",
                        params=filter_dict(
                            {
                                "page_token": page_token,
                                "limit": limit,
                                "order": order,
                                "order_by": order_by,
                                "include_empty": include_empty,
                                "provider_id": provider_id,
                            }
                        ),
                    )
                )
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
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Context).validate_python(
                (await client.get(url=f"/api/v1/contexts/{context_id}")).raise_for_status().json()
            )

    async def update(
        self: Context | str,
        *,
        metadata: Metadata | None,
        client: PlatformClient | None = None,
    ) -> Context:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        context_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            result = pydantic.TypeAdapter(Context).validate_python(
                (await client.put(url=f"/api/v1/contexts/{context_id}", json={"metadata": metadata}))
                .raise_for_status()
                .json()
            )
        if isinstance(self, Context):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def patch_metadata(
        self: Context | str,
        *,
        metadata: MetadataPatch | None,
        client: PlatformClient | None = None,
    ) -> Context:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        context_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            result = pydantic.TypeAdapter(Context).validate_python(
                (await client.patch(url=f"/api/v1/contexts/{context_id}/metadata", json={"metadata": metadata}))
                .raise_for_status()
                .json()
            )
        if isinstance(self, Context):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def delete(
        self: Context | str,
        *,
        client: PlatformClient | None = None,
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `File.delete("123")`
        context_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            _ = (await client.delete(url=f"/api/v1/contexts/{context_id}")).raise_for_status()

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
        async with client or get_platform_client() as client:
            token_response = (
                (
                    await client.post(
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
        return pydantic.TypeAdapter(ContextToken).validate_python({**token_response, "context_id": context_id})

    async def add_history_item(
        self: Context | str,
        *,
        data: Message | Artifact,
        client: PlatformClient | None = None,
    ) -> None:
        """Add a Message or Artifact to the context history (append-only)"""
        target_context_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            _ = (
                await platform_client.post(
                    url=f"/api/v1/contexts/{target_context_id}/history", json=data.model_dump(mode="json")
                )
            ).raise_for_status()

    async def list_history(
        self: Context | str,
        *,
        page_token: str | None = None,
        limit: int | None = None,
        order: Literal["asc"] | Literal["desc"] | None = "asc",
        order_by: Literal["created_at"] | Literal["updated_at"] | None = None,
        client: PlatformClient | None = None,
    ) -> PaginatedResult[ContextHistoryItem]:
        """List all history items for this context in chronological order"""
        target_context_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            return pydantic.TypeAdapter(PaginatedResult[ContextHistoryItem]).validate_python(
                (
                    await platform_client.get(
                        url=f"/api/v1/contexts/{target_context_id}/history",
                        params=filter_dict(
                            {"page_token": page_token, "limit": limit, "order": order, "order_by": order_by}
                        ),
                    )
                )
                .raise_for_status()
                .json()
            )

    async def list_all_history(
        self: Context | str, client: PlatformClient | None = None
    ) -> AsyncIterator[ContextHistoryItem]:
        result = await Context.list_history(self, client=client)
        for item in result.items:
            yield item
        while result.has_more:
            result = await Context.list_history(self, page_token=result.next_page_token, client=client)
            for item in result.items:
                yield item
