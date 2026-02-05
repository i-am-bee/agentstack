# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.platform import File
from agentstack_sdk.server import Server
from agentstack_sdk.util.file import load_file

server = Server()


@server.agent(default_input_modes=["text/plain"], default_output_modes=["text/plain"])
async def example_of_file_processing_example(
    input: Message,
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    """Agent that can accept and modify files"""

    for file_part in input.parts:
        file_part_root = file_part.root

        if file_part_root.kind == "file":
            async with load_file(file_part_root) as loaded_content:
                new_file = await File.create(
                    filename=f"processed_{file_part_root.file.name}",
                    content_type=file_part_root.file.mime_type or "application/octet-stream",
                    content=loaded_content.text.encode(),
                )
                yield new_file.to_file_part()

    yield "File Processing Done"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
