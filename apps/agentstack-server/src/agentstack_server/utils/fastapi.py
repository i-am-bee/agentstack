# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncIterable, Callable

from fastapi import status
from fastapi.staticfiles import StaticFiles
from starlette.responses import AsyncContentStream, Content, StreamingResponse

from agentstack_server.api.schema.common import ErrorStreamResponse, ErrorStreamResponseError
from agentstack_server.utils.utils import extract_messages


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


def encode_stream(chunk: Content) -> str:
    return f"data: {chunk}\n\n"


def _default_encode_exception(ex: Exception) -> str:
    errors = extract_messages(ex)
    if len(errors) == 1:
        [(error, message)] = errors
    else:
        error = "ExceptionGroup"
        message = repr(errors)
    return ErrorStreamResponse(
        error=ErrorStreamResponseError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, type=error, detail=message)
    ).model_dump_json()


def streaming_response(
    content: AsyncContentStream, encode_exception: Callable[[Exception], str] = _default_encode_exception
):
    async def wrapper(stream: AsyncIterable[Content]):
        try:
            async for chunk in stream:
                yield encode_stream(chunk)
        except Exception as ex:
            yield encode_stream(encode_exception(ex))
        finally:
            yield encode_stream("[DONE]")

    return StreamingResponse(
        wrapper(content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
