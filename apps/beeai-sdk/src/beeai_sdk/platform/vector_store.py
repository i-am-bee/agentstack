# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
import uuid
from textwrap import dedent

import httpx
import pydantic

from beeai_sdk.platform import get_client


def validate_metadata(metadata: dict[str, str]) -> dict[str, str]:
    if len(metadata) > 16:
        raise ValueError("Metadata must be less than 16 keys.")
    if any(len(v) > 64 for v in metadata):
        raise ValueError("Metadata keys must be less than 64 characters.")
    if any(len(v) > 512 for v in metadata.values()):
        raise ValueError("Metadata values must be less than 512 characters.")
    return metadata


Metadata = typing.Annotated[
    dict[str, str],
    pydantic.Field(
        description=dedent(
            """
            Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional
            information about the object in a structured format, and querying for objects via API or the dashboard.

            Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of
            512 characters.
            """,
        )
    ),
    pydantic.AfterValidator(validate_metadata),
]


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
        client: httpx.AsyncClient | None = None,
    ) -> VectorStore:
        return pydantic.TypeAdapter(VectorStore).validate_json(
            (
                await (client or get_client()).post(
                    url="/api/v1/vector_stores",
                    json={"name": name, "dimension": dimension, "model_id": model_id},
                )
            )
            .raise_for_status()
            .content
        )

    async def get(
        self: VectorStore | str,
        /,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> VectorStore:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `VectorStore.get("123")` to obtain a new instance
        vector_store_id = self if isinstance(self, str) else self.id
        result = pydantic.TypeAdapter(VectorStore).validate_json(
            (
                await (client or get_client()).get(
                    url=f"/api/v1/vector_stores/{vector_store_id}",
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
        client: httpx.AsyncClient | None = None,
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `VectorStore.delete("123")`
        vector_store_id = self if isinstance(self, str) else self.id
        _ = (
            await (client or get_client()).delete(
                url=f"/api/v1/vector_stores/{vector_store_id}",
            )
        ).raise_for_status()

    async def add_documents(
        self: VectorStore | str, /, items: list[VectorStoreItem], *, client: httpx.AsyncClient | None = None
    ) -> None:
        # `self` has a weird type so that you can call both `instance.add_documents()` or `VectorStore.add_documents("123", items)`
        vector_store_id = self if isinstance(self, str) else self.id
        _ = (
            await (client or get_client()).put(
                url=f"/api/v1/vector_stores/{vector_store_id}",
                json=[item.model_dump(mode="json") for item in items],
            )
        ).raise_for_status()

    async def search(
        self: VectorStore | str,
        /,
        query_vector: list[float],
        *,
        limit: int = 10,
        client: httpx.AsyncClient | None = None,
    ) -> list[VectorStoreSearchResult]:
        # `self` has a weird type so that you can call both `instance.search()` to search within an instance, or `VectorStore.search("123", query_vector)`
        vector_store_id = self if isinstance(self, str) else self.id
        return pydantic.TypeAdapter(list[VectorStoreSearchResult]).validate_python(
            (
                await (client or get_client()).post(
                    url=f"/api/v1/vector_stores/{vector_store_id}/search",
                    json={"query_vector": query_vector, "limit": limit},
                )
            )
            .raise_for_status()
            .json()["items"]
        )

    async def list_documents(
        self: VectorStore | str,
        /,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> list[VectorStoreDocument]:
        # `self` has a weird type so that you can call both `instance.list_documents()` to list documents in an instance, or `VectorStore.list_documents("123")`
        vector_store_id = self if isinstance(self, str) else self.id
        return pydantic.TypeAdapter(list[VectorStoreDocument]).validate_python(
            (await (client or get_client()).get(url=f"/api/v1/vector_stores/{vector_store_id}/documents"))
            .raise_for_status()
            .json()["items"]
        )

    async def delete_document(
        self: VectorStore | str,
        /,
        document_id: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete_document()` or `VectorStore.delete_document("123", "456")`
        vector_store_id = self if isinstance(self, str) else self.id
        _ = (
            await (client or get_client()).delete(
                url=f"/api/v1/vector_stores/{vector_store_id}/documents/{document_id}",
            )
        ).raise_for_status()
