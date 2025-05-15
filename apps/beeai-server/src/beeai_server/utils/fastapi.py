# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse, AsyncContentStream
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

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
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR, type=error, detail=message
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
