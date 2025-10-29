# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
import uuid
from typing import Literal

import pydantic

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.platform.types import Metadata


class VectorStoreStats(pydantic.BaseModel):
    usage_bytes: int
    num_documents: int


class VectorStoreDocument(pydantic.BaseModel):
    id: str
    vector_store_id: str
    file_id: str | None = None
    usage_bytes: int | None = None
    created_at: pydantic.AwareDatetime


class VectorStoreItem(pydantic.BaseModel):
    id: str = pydantic.Field(default_factory=lambda: uuid.uuid4().hex)
    document_id: str
    document_type: typing.Literal["platform_file", "external"] = "platform_file"
    model_id: str | typing.Literal["platform"] = "platform"
    text: str
    embedding: list[float]
    metadata: Metadata | None = None


class VectorStoreSearchResult(pydantic.BaseModel):
    item: VectorStoreItem
    score: float


class VectorStore(pydantic.BaseModel):
    id: str
    name: str | None = None
    model_id: str
    dimension: int
    created_at: pydantic.AwareDatetime
    last_active_at: pydantic.AwareDatetime
    created_by: str
    stats: VectorStoreStats | None = None

    @staticmethod
    async def create(
        *,
        name: str,
        dimension: int,
        model_id: str,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> VectorStore:
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(VectorStore).validate_json(
                (
                    await platform_client.post(
                        url="/api/v1/vector_stores",
                        json={"name": name, "dimension": dimension, "model_id": model_id},
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .content
            )

    async def get(
        self: VectorStore | str,
        /,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> VectorStore:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `VectorStore.get("123")` to obtain a new instance
        vector_store_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            result = pydantic.TypeAdapter(VectorStore).validate_json(
                (
                    await platform_client.get(
                        url=f"/api/v1/vector_stores/{vector_store_id}",
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .content
            )
        if isinstance(self, VectorStore):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def delete(
        self: VectorStore | str,
        /,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `VectorStore.delete("123")`
        vector_store_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            _ = (
                await platform_client.delete(
                    url=f"/api/v1/vector_stores/{vector_store_id}",
                    params=context_id and {"context_id": context_id},
                )
            ).raise_for_status()

    async def add_documents(
        self: VectorStore | str,
        /,
        items: list[VectorStoreItem],
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> None:
        # `self` has a weird type so that you can call both `instance.add_documents()` or `VectorStore.add_documents("123", items)`
        vector_store_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            _ = (
                await platform_client.put(
                    url=f"/api/v1/vector_stores/{vector_store_id}",
                    json=[item.model_dump(mode="json") for item in items],
                    params=context_id and {"context_id": context_id},
                )
            ).raise_for_status()

    async def search(
        self: VectorStore | str,
        /,
        query_vector: list[float],
        *,
        limit: int = 10,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> list[VectorStoreSearchResult]:
        # `self` has a weird type so that you can call both `instance.search()` to search within an instance, or `VectorStore.search("123", query_vector)`
        vector_store_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(list[VectorStoreSearchResult]).validate_python(
                (
                    await platform_client.post(
                        url=f"/api/v1/vector_stores/{vector_store_id}/search",
                        json={"query_vector": query_vector, "limit": limit},
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .json()["items"]
            )

    async def list_documents(
        self: VectorStore | str,
        /,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> list[VectorStoreDocument]:
        # `self` has a weird type so that you can call both `instance.list_documents()` to list documents in an instance, or `VectorStore.list_documents("123")`
        vector_store_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(list[VectorStoreDocument]).validate_python(
                (
                    await platform_client.get(
                        url=f"/api/v1/vector_stores/{vector_store_id}/documents",
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .json()["items"]
            )

    async def delete_document(
        self: VectorStore | str,
        /,
        document_id: str,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete_document()` or `VectorStore.delete_document("123", "456")`
        vector_store_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            _ = (
                await platform_client.delete(
                    url=f"/api/v1/vector_stores/{vector_store_id}/documents/{document_id}",
                    params=context_id and {"context_id": context_id},
                )
            ).raise_for_status()
