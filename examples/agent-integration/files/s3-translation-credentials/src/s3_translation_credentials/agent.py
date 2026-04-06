# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import FilePart, FileWithUri, Message, Part, TextPart
from agentstack_sdk.a2a.extensions.storage.s3_credentials import S3CredentialsExtensionServer, S3CredentialsExtensionSpec
from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.util.file import load_file

server = Server()


@server.agent(
    name="s3-translation-credentials-agent",
    description=(
        "Accepts a plain-text file, mock-translates it (reverses each line), "
        "and uploads the result using injected S3 credentials. "
        "Returns a presigned GET URL for the translated file — no S3 SDK needed by the caller."
    ),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)
async def translate_agent(
    input: Message,
    context: RunContext,
    s3: Annotated[S3CredentialsExtensionServer, S3CredentialsExtensionSpec()],
):
    await context.store(input)

    for part in input.parts:
        if isinstance(part.root, FilePart):
            async with load_file(part.root) as loaded:
                original_text = loaded.text

            # Mock "translation": reverse each line
            translated = "\n".join(line[::-1] for line in original_text.splitlines())

            # Agent decides the filename; upload() handles key construction and
            # returns a presigned GET URL — the caller never needs an S3 SDK.
            download_url = await s3.upload("translated.txt", translated.encode(), "text/plain")

            chunk = AgentArtifact(
                parts=[
                    TextPart(text="Here is the translated document."),
                    FilePart(
                        file=FileWithUri(
                            uri=download_url,
                            mime_type="text/plain",
                            name="translated.txt",
                        )
                    ),
                ]
            )
            await context.store(chunk)
            yield chunk
            return

    response = AgentMessage(parts=[TextPart(text="No file found in input.")])
    await context.store(response)
    yield response


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    run()
