# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

import pydantic
from a2a.types import FilePart, FileWithUri

from beeai_sdk.platform.client import PlatformClient, get_platform_client
from beeai_sdk.util.file import LoadedFile, LoadedFileWithUri, PlatformFileUrl


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

    @property
    def url(self) -> PlatformFileUrl:
        return PlatformFileUrl(f"beeai://{self.id}")

    @staticmethod
    async def create(
        *,
        filename: str,
        content: typing.BinaryIO | bytes,
        content_type: str = "application/octet-stream",
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> File:
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(File).validate_python(
                (
                    await platform_client.post(
                        url="/api/v1/files",
                        files={"file": (filename, content, content_type)},
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .json()
            )

    async def get(
        self: File | str,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> File:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `File.get("123")` to obtain a new instance
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(File).validate_python(
                (
                    await platform_client.get(
                        url=f"/api/v1/files/{file_id}",
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .json()
            )

    async def delete(
        self: File | str,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `File.delete("123")`
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            _ = (
                await platform_client.delete(
                    url=f"/api/v1/files/{file_id}", params=context_id and {"context_id": context_id}
                )
            ).raise_for_status()

    @asynccontextmanager
    async def load_content(
        self: File | str,
        *,
        stream: bool = False,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> AsyncIterator[LoadedFile]:
        # `self` has a weird type so that you can call both `instance.load_content()` to create an extraction for an instance, or `File.load_content("123")`
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id

            file = await File.get(file_id, client=client, context_id=context_id) if isinstance(self, str) else self

            async with platform_client.stream(
                "GET", url=f"/api/v1/files/{file_id}/content", params=context_id and {"context_id": context_id}
            ) as response:
                response.raise_for_status()
                if not stream:
                    await response.aread()
                yield LoadedFileWithUri(response=response, filename=file.filename)

    @asynccontextmanager
    async def load_text_content(
        self: File | str,
        *,
        stream: bool = False,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> AsyncIterator[LoadedFile]:
        # `self` has a weird type so that you can call both `instance.load_text_content()` to create an extraction for an instance, or `File.load_text_content("123")`
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id

            file = await File.get(file_id, client=client, context_id=context_id) if isinstance(self, str) else self

            async with platform_client.stream(
                "GET",
                url=f"/api/v1/files/{file_id}/text_content",
                params=context_id and {"context_id": context_id},
            ) as response:
                response.raise_for_status()
                if not stream:
                    await response.aread()
                yield LoadedFileWithUri(response=response, filename=file.filename)

    async def create_extraction(
        self: File | str,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> Extraction:
        # `self` has a weird type so that you can call both `instance.create_extraction()` to create an extraction for an instance, or `File.create_extraction("123")`
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(Extraction).validate_python(
                (
                    await platform_client.post(
                        url=f"/api/v1/files/{file_id}/extraction",
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .json()
            )

    async def get_extraction(
        self: File | str,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> Extraction:
        # `self` has a weird type so that you can call both `instance.get_extraction()` to get an extraction of an instance, or `File.get_extraction("123", "456")`
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            return pydantic.TypeAdapter(Extraction).validate_python(
                (
                    await platform_client.get(
                        url=f"/api/v1/files/{file_id}/extraction",
                        params=context_id and {"context_id": context_id},
                    )
                )
                .raise_for_status()
                .json()
            )

    async def delete_extraction(
        self: File | str,
        *,
        client: PlatformClient | None = None,
        context_id: str | None | Literal["auto"] = "auto",
    ) -> None:
        # `self` has a weird type so that you can call both `instance.delete_extraction()` or `File.delete_extraction("123", "456")`
        file_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as platform_client:
            context_id = platform_client.context_id if context_id == "auto" else context_id
            _ = (
                await platform_client.delete(
                    url=f"/api/v1/files/{file_id}/extraction",
                    params=context_id and {"context_id": context_id},
                )
            ).raise_for_status()

    def to_file_part(self: File) -> FilePart:
        return FilePart(file=FileWithUri(name=self.filename, uri=f"beeai://{self.id}"))
