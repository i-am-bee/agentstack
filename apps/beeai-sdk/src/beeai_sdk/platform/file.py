# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import httpx
import pydantic

from beeai_sdk.platform.context import get_platform_client


class Extraction(pydantic.BaseModel):
    id: str
    file_id: str
    extracted_file_id: str | None = None
    status: typing.Literal["pending", "in_progress", "completed", "failed", "cancelled"] = "pending"
    job_id: str | None = None
    error_message: str | None = None
    extraction_metadata: dict[str, typing.Any] | None = None
    started_at: pydantic.AwareDatetime | None = None
    finished_at: pydantic.AwareDatetime | None = None
    created_at: pydantic.AwareDatetime


class File(pydantic.BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    created_at: pydantic.AwareDatetime
    created_by: str
    file_type: typing.Literal["user_upload", "extracted_text"]
    parent_file_id: str | None = None

    @staticmethod
    async def create(
        *,
        filename: str,
        content: typing.BinaryIO | bytes,
        content_type: str = "application/octet-stream",
        client: httpx.AsyncClient | None = None,
    ) -> File:
        return pydantic.TypeAdapter(File).validate_python(
            (
                await (client or get_platform_client()).post(
                    url="/api/v1/files",
                    files={"file": (filename, content, content_type)},
                )
            )
            .raise_for_status()
            .json()
        )

    async def get(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> File:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        file_id = self if isinstance(self, str) else self.id
        return pydantic.TypeAdapter(File).validate_python(
            (await (client or get_platform_client()).get(url=f"/api/v1/files/{file_id}")).raise_for_status().json()
        )

    async def delete(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `File.delete("123")`
        file_id = self if isinstance(self, str) else self.id
        _ = (await (client or get_platform_client()).delete(url=f"/api/v1/files/{file_id}")).raise_for_status()

    async def content(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> str:
        # `self` has a weird type so that you can call both `instance.content()` to get content of an instance, or `File.content("123")`
        file_id = self if isinstance(self, str) else self.id
        return (
            (await (client or get_platform_client()).get(url=f"/api/v1/files/{file_id}/content"))
            .raise_for_status()
            .text
        )

    async def text_content(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> str:
        # `self` has a weird type so that you can call both `instance.text_content()` to get text content of an instance, or `File.text_content("123")`
        file_id = self if isinstance(self, str) else self.id
        return (
            (await (client or get_platform_client()).get(url=f"/api/v1/files/{file_id}/text_content"))
            .raise_for_status()
            .text
        )

    async def create_extraction(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> Extraction:
        # `self` has a weird type so that you can call both `instance.create_extraction()` to create an extraction for an instance, or `File.create_extraction("123")`
        file_id = self if isinstance(self, str) else self.id
        return pydantic.TypeAdapter(Extraction).validate_python(
            (
                await (client or get_platform_client()).post(
                    url=f"/api/v1/files/{file_id}/extraction",
                )
            )
            .raise_for_status()
            .json()
        )

    async def get_extraction(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> Extraction:
        # `self` has a weird type so that you can call both `instance.get_extraction()` to get an extraction of an instance, or `File.get_extraction("123", "456")`
        file_id = self if isinstance(self, str) else self.id
        return pydantic.TypeAdapter(Extraction).validate_python(
            (
                await (client or get_platform_client()).get(
                    url=f"/api/v1/files/{file_id}/extraction",
                )
            )
            .raise_for_status()
            .json()
        )

    async def delete_extraction(
        self: File | str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete_extraction()` or `File.delete_extraction("123", "456")`
        file_id = self if isinstance(self, str) else self.id
        _ = (
            await (client or get_platform_client()).delete(url=f"/api/v1/files/{file_id}/extraction")
        ).raise_for_status()
