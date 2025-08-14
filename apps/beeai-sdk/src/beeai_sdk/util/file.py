# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import typing
from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack, asynccontextmanager
from functools import cached_property
from typing import Protocol

import httpx
from a2a.types import FilePart, FileWithBytes, FileWithUri
from httpx._decoders import LineDecoder
from pydantic import AnyUrl, HttpUrl, RootModel, UrlConstraints


class LoadedFile(Protocol):
    filename: str | None
    content_type: str
    file_size_bytes: int | None

    @property
    def content(self) -> bytes: ...
    @property
    def text(self) -> str: ...

    def read(self) -> bytes:
        """
        Read and return the response content.
        """
        ...

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        """
        A byte-iterator over the decoded response content.
        This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
        """
        yield b""

    def iter_text(self, chunk_size: int | None = None) -> Iterator[str]:
        """
        A str-iterator over the decoded response content
        that handles both gzip, deflate, etc but also detects the content's
        string encoding.
        """
        yield ""

    def iter_lines(self) -> Iterator[str]:
        yield ""

    async def aread(self) -> bytes: ...

    async def aiter_bytes(self, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        """
        A byte-iterator over the decoded response content.
        This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
        """
        yield b""

    async def aiter_text(self, chunk_size: int | None = None) -> AsyncIterator[str]:
        """
        A str-iterator over the decoded response content
        that handles both gzip, deflate, etc but also detects the content's
        string encoding.
        """
        yield ""

    async def aiter_lines(self) -> AsyncIterator[str]:
        yield ""


class LoadedFileWithBytes(LoadedFile):
    _content: bytes

    def __init__(
        self,
        content: bytes,
        filename: str | None = None,
        content_type: str | None = None,
        encoding: str | None = None,
    ):
        self.filename = filename
        self.content_type = content_type or "application/octet-stream"
        self.file_size_bytes = len(content)
        self._content = content
        self._encoding = encoding or "utf-8"

    @property
    def content(self) -> bytes:
        return self._content

    @cached_property
    def text(self) -> str:  # pyright: ignore [reportIncompatibleMethodOverride]
        return self._content.decode(self._encoding)

    def read(self) -> bytes:
        return b"".join(self.iter_bytes())

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        chunk_size = len(self._content) if chunk_size is None else chunk_size
        for i in range(0, len(self._content), max(chunk_size, 1)):
            yield self._content[i : i + chunk_size]

    def iter_text(self, chunk_size: int | None = None) -> Iterator[str]:
        chunk_size = len(self._content) if chunk_size is None else chunk_size
        for i in range(0, len(self._content), max(chunk_size, 1)):
            yield self.text[i : i + chunk_size]

    def iter_lines(self) -> typing.Iterator[str]:
        decoder = LineDecoder()
        for text in self.iter_text():
            for line in decoder.decode(text):
                yield line
        for line in decoder.flush():
            yield line

    async def aread(self) -> bytes:
        return self._content

    async def aiter_bytes(self, chunk_size: int | None = None) -> typing.AsyncIterator[bytes]:
        for chunk in self.iter_bytes(chunk_size):
            yield chunk

    async def aiter_text(self, chunk_size: int | None = None) -> typing.AsyncIterator[str]:
        for chunk in self.iter_text(chunk_size):
            yield chunk

    async def aiter_lines(self) -> typing.AsyncIterator[str]:
        for line in self.iter_lines():
            yield line


class LoadedFileWithUri:
    _response: httpx.Response  # a (potentially still opened) response object

    def __init__(
        self,
        response: httpx.Response,
        filename: str | None = None,
        content_type: str | None = None,
        file_size_bytes: int | None = None,
    ):
        self._response = response

        response_filename = self._response.headers.get("Content-Disposition", "").split("filename=")[-1]
        response_content_type = self._response.headers.get("Content-Type", "application/octet-stream")

        self.file_size_bytes = file_size_bytes or int(response.headers.get("Content-Length", "0")) or None
        self.filename = filename or response_filename
        self.content_type = content_type or response_content_type or "application/octet-stream"
        self._response = response

    @property
    def content(self) -> bytes:
        return self._response.content

    @property
    def text(self) -> str:
        return self._response.text

    def read(self) -> bytes:
        """
        Read and return the response content.
        """
        return self._response.read()

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        """
        A byte-iterator over the decoded response content.
        This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
        """
        yield from self._response.iter_bytes(chunk_size)

    def iter_text(self, chunk_size: int | None = None) -> Iterator[str]:
        """
        A str-iterator over the decoded response content
        that handles both gzip, deflate, etc but also detects the content's
        string encoding.
        """
        yield from self._response.iter_text(chunk_size)

    def iter_lines(self) -> Iterator[str]:
        yield from self._response.iter_lines()

    async def aread(self) -> bytes:
        """
        Read and return the response content.
        """
        return await self._response.aread()

    async def aiter_bytes(self, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        """
        A byte-iterator over the decoded response content.
        This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
        """
        async for chunk in self._response.aiter_bytes(chunk_size):
            yield chunk

    async def aiter_text(self, chunk_size: int | None = None) -> AsyncIterator[str]:
        """
        A str-iterator over the decoded response content
        that handles both gzip, deflate, etc but also detects the content's
        string encoding.
        """
        async for chunk in self._response.aiter_text(chunk_size):
            yield chunk

    async def aiter_lines(self) -> AsyncIterator[str]:
        async for line in self._response.aiter_lines():
            yield line


class PlatformFileUrl(AnyUrl):
    _constraints = UrlConstraints(allowed_schemes=["beeai"])


UriType = RootModel[PlatformFileUrl | HttpUrl]


@asynccontextmanager
async def load_file(
    part: FilePart,
    stream: bool = False,
    client: httpx.AsyncClient | None = None,
) -> AsyncIterator[LoadedFile]:
    """
    :param stream: if stream is set to False, 'content' and 'text' fields are immediately available.
        Otherwise, they are only available after calling the '(a)read' method.
    """
    match part.file:
        case FileWithUri(mime_type=content_type, name=filename, uri=uri):
            match UriType.model_validate(uri).root:
                case PlatformFileUrl() as url:
                    from beeai_sdk.platform import File

                    file_id = url.host
                    assert file_id

                    async with File.load_content(file_id, stream=stream) as file:
                        # override filename and content_type from part
                        if filename:
                            file.filename = filename
                        if content_type:
                            file.content_type = content_type
                        yield file
                case HttpUrl():
                    async with AsyncExitStack() as stack:
                        if client is None:
                            client = await stack.enter_async_context(httpx.AsyncClient())
                        async with client.stream("GET", uri) as response:
                            response.raise_for_status()
                            file = LoadedFileWithUri(response=response, filename=filename, content_type=content_type)
                            if not stream:
                                await file.aread()
                            yield file

        case FileWithBytes(bytes=content, name=filename, mime_type=content_type):
            yield LoadedFileWithBytes(content=base64.b64decode(content), filename=filename, content_type=content_type)
