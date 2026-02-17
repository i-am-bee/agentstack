# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import FilePart, Message
from agentstack_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.platform import File
from agentstack_sdk.server import Server
from agentstack_sdk.util.file import load_file

server = Server()


@server.agent(
    default_input_modes=["text/plain", "application/pdf", "image/*"],
    default_output_modes=["text/plain", "application/pdf", "image/*"],
)
async def file_processing_example(
    input: Message,
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    """Agent that handles both text and binary files"""

    for file_part in input.parts:
        file_part_root = file_part.root

        if isinstance(file_part_root, FilePart):
            mime_type = file_part_root.file.mime_type or "application/octet-stream"

            async with load_file(file_part_root) as loaded_content:
                # Determine if file is text or binary based on MIME type
                is_text_file = mime_type.startswith("text/") or mime_type in [
                    "application/json",
                    "application/xml",
                    "text/xml",
                ]

                if is_text_file:
                    # For text files, use .text and encode to bytes
                    content = loaded_content.text.encode()
                else:
                    # For binary files (PDFs, images, etc.), use .content directly
                    content = loaded_content.content

                # Create new file with appropriate content
                new_file = await File.create(
                    filename=f"processed_{file_part_root.file.name}",
                    content_type=mime_type,
                    content=content,
                )
                yield new_file.to_file_part()

    yield "File processing complete"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
