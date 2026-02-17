# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated, cast

from a2a.types import Message
from agentstack_sdk.a2a.extensions.ui.error import (
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
)
from agentstack_sdk.server import Server
from pydantic import JsonValue

server = Server()


@server.agent()
async def adding_error_context_example(
    input: Message,
    error_ext: Annotated[
        ErrorExtensionServer, ErrorExtensionSpec(params=ErrorExtensionParams(include_stacktrace=False))
    ],
):
    # Add context before an error might occur or in an except block
    ctx = cast(dict[str, JsonValue], error_ext.context)
    ctx["request_id"] = "req-123"
    ctx["user_id"] = 42

    # ... do work ...

    # If an exception is raised, the context is included
    raise ValueError("Something went wrong!")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
