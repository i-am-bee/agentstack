# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncIterable

from httpx import AsyncClient
from pydantic import AnyUrl

from beeai_server.configuration import DoclingExtractionConfiguration
from beeai_server.domain.models.file import AsyncFile
from beeai_server.domain.repositories.file import ITextExtractionBackend
from beeai_server.utils.utils import extract_string_value_stream


class DoclingTextExtractionBackend(ITextExtractionBackend):
    def __init__(self, config: DoclingExtractionConfiguration):
        self._config = config
        self._enabled = config.enabled

    @asynccontextmanager
    async def extract_text(self, *, file_url: AnyUrl, timeout: timedelta | None = None) -> AsyncIterable[AsyncFile]:
        if not self._enabled:
            raise RuntimeError(
                "Docling extraction backend is not enabled, please check the documentation how to enable it"
            )

        timeout = timeout or timedelta(minutes=5)
        async with AsyncClient(base_url=str(self._config.docling_service_url), timeout=timeout.seconds) as client:
            async with client.stream(
                "POST",
                "/v1alpha/convert/source",
                json={
                    "options": {
                        "to_formats": ["md"],
                        "document_timeout": timeout.total_seconds(),
                        "image_export_mode": "placeholder",
                    },
                    "http_sources": [{"url": str(file_url)}],
                },
            ) as response:
                response.raise_for_status()

                md_stream = None

                async def read(chunk_size: int = 1024) -> bytes:
                    nonlocal md_stream
                    if not md_stream:
                        md_stream = extract_string_value_stream(response.aiter_text, "md_content", chunk_size)
                    async for text_chunk in md_stream:
                        return text_chunk.encode("utf-8")
                    return b""

                yield AsyncFile(
                    filename="extracted_text.md",
                    content_type="text/markdown",
                    read=read,
                    size=None,  # size is unknown beforehand
                )
