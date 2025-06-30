# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Callable, Protocol

from fastapi import HTTPException
from fastapi import status
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse, AsyncContentStream
from typing_extensions import Doc, Awaitable

from beeai_server.api.schema.common import ErrorStreamResponseError, ErrorStreamResponse
from beeai_server.utils.utils import extract_messages


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


def encode_stream(chunk: str) -> str:
    return f"data: {chunk}\n\n"


def streaming_response(content: AsyncContentStream):
    async def wrapper(stream):
        try:
            async for chunk in stream:
                yield encode_stream(chunk)
        except Exception as ex:
            errors = extract_messages(ex)
            if len(errors) == 1:
                [(error, message)] = errors
            else:
                error = "ExceptionGroup"
                message = repr(errors)
            yield encode_stream(
                ErrorStreamResponse(
                    error=ErrorStreamResponseError(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, type=error, detail=message
                    )
                ).model_dump_json()
            )

    return StreamingResponse(
        wrapper(content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


def _entity_too_large(max_size: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=(
            f"File size exceeds the limit of {max_size / 1024 / 1024:.2f} MB. "
            f"Either the file is too large or you exceeded the available storage capacity."
        ),
    )


class AsyncFileProtocol(Protocol):
    async def read(self, size: int) -> bytes: ...


def limit_size_wrapper(
    read: Callable[[int], Awaitable[bytes]], max_size: int = None, size: int | None = None
) -> Callable[[int], Awaitable[bytes]]:
    current_size = 0

    # Quick check using the Content-Length header. This is not fully reliable as the header can be omitted or incorrect,
    # but it can reject large files early.
    if max_size is not None and size is not None and size > max_size:
        raise _entity_too_large(max_size)

    async def _read(size: Annotated[int, Doc("The number of bytes to read from the file.")] = -1) -> bytes:
        nonlocal current_size
        if max_size is None:
            return await read(size)

        if chunk := await read(size):
            current_size += len(chunk)
            if current_size > max_size:
                raise _entity_too_large(max_size)
        return chunk

    return _read
