# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.ui.error import (
    ErrorExtensionParams,
    ErrorExtensionServer,
    ErrorExtensionSpec,
)
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def advanced_error_reporting_example(
    input: Message,
    # Configure to include stack traces
    error_ext: Annotated[
        ErrorExtensionServer,
        ErrorExtensionSpec(params=ErrorExtensionParams(include_stacktrace=True)),
    ],
):
    """Agent that demonstrates error handling with stack traces"""
    yield "Working..."

    # This exception will be caught and formatted by the extension
    # The stack trace will be included because of the configuration above
    raise ValueError("Something went wrong!")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
