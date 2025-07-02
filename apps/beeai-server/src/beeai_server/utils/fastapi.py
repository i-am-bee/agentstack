# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from fastapi import status
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse, AsyncContentStream

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
