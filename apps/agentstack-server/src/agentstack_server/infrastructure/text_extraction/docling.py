# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal
from typing import NamedTuple, cast

import ijson
import orjson
from httpx import AsyncClient as HttpxAsyncClient
from pydantic import AnyUrl

from agentstack_server.configuration import DoclingExtractionConfiguration
from agentstack_server.domain.models.file import AsyncFile, ExtractionFormat, TextExtractionSettings
from agentstack_server.domain.repositories.file import ITextExtractionBackend

logger = logging.getLogger(__name__)


class DoclingFormatInfo(NamedTuple):
    api_option: str
    file_extension: str
    response_field_key: str
    content_type: str


_DOCLING_FORMAT_INFO: dict[ExtractionFormat, DoclingFormatInfo] = {
    ExtractionFormat.MARKDOWN: DoclingFormatInfo("md", "md", "md_content", "text/markdown"),
    ExtractionFormat.VENDOR_SPECIFIC_JSON: DoclingFormatInfo("json", "json", "json_content", "application/json"),
}


async def _process_docling_stream(
    async_file: AsyncFile, formats: list[ExtractionFormat]
) -> AsyncIterator[tuple[AsyncFile, ExtractionFormat]]:
    key_map = {info.response_field_key: (fmt, info) for fmt, info in _DOCLING_FORMAT_INFO.items() if fmt in formats}

    def serialize(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

    async for k, v in ijson.kvitems_async(async_file, "document", use_float=False):  # pyright: ignore[reportAny]
        if k in key_map:
            fmt, info = key_map[k]

            content = v.encode("utf-8") if isinstance(v, str) else cast(bytes, orjson.dumps(v, default=serialize))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            async_file = AsyncFile.from_bytes(
                filename=f"extracted_response.{info.file_extension}",
                content_type=info.content_type,
                content=content,
            )

            yield (async_file, fmt)


class DoclingTextExtractionBackend(ITextExtractionBackend):
    """
    # TODO: [DISCLAIMER] this is loading entire field value to memory (which in case of docling is entire document)
    # Implementing a streaming parser has been deemed too complex, instead the text extraction worker should be
    # scaled independently with memory bounded by concurrency and max_single_file_size configuration
    """

    def __init__(self, config: DoclingExtractionConfiguration):
        self._config = config
        self._enabled = config.enabled

    @property
    def backend_name(self) -> str:
        """Return the name of the extraction backend."""
        return "docling"

    @asynccontextmanager
    async def extract_text(
        self,
        *,
        file_url: AnyUrl,
        timeout: timedelta | None = None,  # noqa: ASYNC109
        settings: TextExtractionSettings | None = None,
    ) -> AsyncIterator[AsyncIterator[tuple[AsyncFile, ExtractionFormat]]]:
        """
        Extract text from a file using the Docling service.
        Streams the response and yields files as they are parsed.
        """
        if not self._enabled:
            raise RuntimeError(
                "Docling extraction backend is not enabled, please check the documentation how to enable it"
            )

        formats = settings.formats if settings else [ExtractionFormat.MARKDOWN, ExtractionFormat.VENDOR_SPECIFIC_JSON]

        timeout = timeout or timedelta(minutes=5)

        async with (
            HttpxAsyncClient(base_url=str(self._config.docling_service_url), timeout=timeout.seconds) as client,
            client.stream(
                "POST",
                "/v1/convert/source",
                json={
                    "options": {
                        "to_formats": [_DOCLING_FORMAT_INFO[fmt].api_option for fmt in formats],
                        "document_timeout": timeout.total_seconds(),
                        "image_export_mode": "placeholder",
                    },
                    "sources": [{"kind": "http", "url": str(file_url)}],
                },
            ) as response,
        ):
            response.raise_for_status()  # pyright: ignore[reportUnusedCallResult]
            async_file = AsyncFile.from_async_iterator(response.aiter_bytes(), "tmp", "application/json")
            yield _process_docling_stream(async_file, formats)
