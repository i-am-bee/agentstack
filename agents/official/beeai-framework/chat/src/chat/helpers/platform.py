# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from acp_sdk import MessagePart
import httpx
from pydantic import AnyUrl, BaseModel, parse_obj_as


class FileInfo(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    created_at: str
    created_by: str
    file_type: str
    parent_file_id: str | None = None


class ApiClient:
    API_VERSION = "/api/v1"

    @staticmethod
    def get_platform_base_url() -> str:
        return os.getenv("PLATFORM_URL", "http://127.0.0.1:8333").rstrip("/")

    @classmethod
    def get_api_base_url(cls) -> str:
        return cls.get_platform_base_url() + cls.API_VERSION

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or self.get_api_base_url()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        response = await self._client.post(endpoint, **kwargs)
        response.raise_for_status()
        return response

    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        response = await self._client.get(endpoint, **kwargs)
        response.raise_for_status()
        return response


async def get_file_info(file_id: str) -> FileInfo | None:
    async with ApiClient() as api:
        response = await api.get(f"/files/{file_id}")
        return FileInfo.model_validate(response.json())


async def read_file(
    file_url: AnyUrl,
) -> MessagePart:
    print(f"Reading file from {file_url}...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(str(file_url))
        content_type = resp.headers.get("Content-Type")
        return MessagePart(content=resp.content.decode(), content_type=content_type)


async def upload_file(filename: str, content_type: str, content: bytes) -> FileInfo:
    async with ApiClient() as api:
        files = {"file": (filename, content, content_type)}
        response = await api.post("/files", files=files)
        return FileInfo.model_validate(response.json()) 

def get_file_url(file_id: str) -> AnyUrl:
    full_url = f"{ApiClient.get_api_base_url()}/files/{file_id}/content"
    return parse_obj_as(AnyUrl, full_url)