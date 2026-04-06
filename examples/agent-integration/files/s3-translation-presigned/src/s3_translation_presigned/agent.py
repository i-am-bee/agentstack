# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# NOTE: On-demand slot requests
# The pre-signed URL model requires the client to declare every output file
# upfront, before sending the message. The agent can only write to the slots it
# was given — it cannot request new upload URLs mid-stream.
#
# If the number of output files is not known ahead of time (e.g. the agent
# splits a document into an unknown number of chunks), use the S3 credentials
# extension instead: the client injects short-lived IAM-scoped credentials and
# the agent can create as many objects as it needs within its assigned prefix.
# See: examples/agent-integration/files/s3-translation-credentials/

import os
from typing import Annotated

from a2a.types import FilePart, FileWithUri, Message, Part, TextPart
from agentstack_sdk.a2a.extensions.storage.s3 import S3ExtensionServer, S3ExtensionSpec
from agentstack_sdk.a2a.types import AgentArtifact, AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.util.file import load_file

server = Server()


@server.agent(
    name="s3-translation-agent",
    description=(
        "Accepts a plain-text file, mock-translates it (reverses each line), "
        "and uploads two result files via the S3 extension: the translated text "
        "and a stats summary. Returns pre-signed download URLs for both."
    ),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)
async def translate_agent(
    input: Message,
    context: RunContext,
    s3: Annotated[S3ExtensionServer, S3ExtensionSpec()],
):
    await context.store(input)
    files_found = False

    for part in input.parts:
        if isinstance(part.root, FilePart):
            async with load_file(part.root) as loaded:
                original_text = loaded.text

            lines = original_text.splitlines()

            # Output 1 — mock "translation": reverse each line
            translated = "\n".join(line[::-1] for line in lines)
            translated_url = await s3.upload(
                slot="translated",
                content=translated.encode(),
                content_type="text/plain",
            )

            # Output 2 — plain-text stats summary
            word_count = sum(len(line.split()) for line in lines)
            summary = (
                f"lines:  {len(lines)}\n"
                f"words:  {word_count}\n"
                f"chars:  {len(original_text)}\n"
            )
            summary_url = await s3.upload(
                slot="summary",
                content=summary.encode(),
                content_type="text/plain",
            )

            chunk = AgentArtifact(
                parts=[
                    TextPart(text="Translation and summary are ready."),
                    FilePart(file=FileWithUri(
                        uri=translated_url,
                        mime_type="text/plain",
                        name=f"translated_{part.root.file.name or 'unknown'}.txt",
                    )),
                    FilePart(file=FileWithUri(
                        uri=summary_url,
                        mime_type="text/plain",
                        name="summary.txt",
                    )),
                ]
            )
            await context.store(chunk)
            yield chunk
            files_found = True

    if not files_found:
        response = AgentMessage(parts=[TextPart(text="No file found in input.")])
        await context.store(response)
        yield response


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    run()
