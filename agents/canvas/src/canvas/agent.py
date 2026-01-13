# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message, TextPart
from agentstack_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    CanvasExtensionServer,
    CanvasExtensionSpec,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentArtifact
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.middleware.platform_auth_backend import PlatformAuthBackend
from openai import AsyncOpenAI

server = Server()


@server.agent(
    name="Canvas",
    documentation_url=f"https://github.com/i-am-bee/agentstack/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/canvas",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    description="A minimal canvas agent capable of iterating on an artifact.",
    detail=AgentDetail(
        interaction_mode="multi-turn",
        author=AgentDetailContributor(name="IBM"),
    ),
)
async def canvas_agent(
    message: Message,
    context: RunContext,
    canvas: Annotated[CanvasExtensionServer, CanvasExtensionSpec()],
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
):
    await context.store(message)
    edit_request = await canvas.parse_canvas_edit_request(message=message)

    user_text_content = ""
    if message.parts:
        for part in message.parts:
            if isinstance(part.root, TextPart):
                user_text_content = part.root.text
                break

    if not user_text_content and not edit_request:
        yield "Hi, how can I help you?"
        return

    (llm_config,) = llm.data.llm_fulfillments.values()
    client = AsyncOpenAI(
        api_key=llm_config.api_key,
        base_url=llm_config.api_base,
    )

    if edit_request:
        original_content = ""
        for part in edit_request.artifact.parts:
            if isinstance(part.root, TextPart):
                original_content = part.root.text
                break
        selected_text = original_content[edit_request.start_index:edit_request.end_index]
        system_prompt = f"""You are an expert content editor. The user has selected a part of a larger text and wants to edit it.

The user's instruction is: "{edit_request.description}"

The text selection to be edited is:
---
{selected_text}
---

This selection is part of the following full document:
---
{original_content}
---

Your task is to apply the user's instruction ONLY to the selected text and then return the ENTIRE document with just that selection modified. Do not add any extra commentary or explanation.
"""
        user_prompt = edit_request.description
        artifact = AgentArtifact(
            name=f"Edited - {edit_request.artifact.name}",
            parts=[TextPart(text="")],
        )
    else:
        system_prompt = "You are a helpful assistant. Output only the requested text, without any additional explanation or preamble. Use Markdown syntax in your output. Be mindful of the need for double new lines in order to make a new line."
        user_prompt = user_text_content
        artifact = AgentArtifact(
            name="Response",
            parts=[TextPart(text="")],
        )

    yield artifact

    stream = await client.chat.completions.create(
        model=llm_config.api_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )

    buffer = ""
    async for chunk in stream:
        if not chunk.choices:
            continue
        content_delta = chunk.choices[0].delta.content or ""
        if content_delta:
            buffer += content_delta
            yield AgentArtifact(
                artifact_id=artifact.artifact_id,
                name=artifact.name,
                parts=[TextPart(text=content_delta)],
            )

    final_artifact = AgentArtifact(
        artifact_id=artifact.artifact_id,
        name=artifact.name,
        parts=[TextPart(text=buffer)],
    )
    await context.store(final_artifact)


def serve():
    try:
        server.run(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 10002)),
            configure_telemetry=True,
            auth_backend=PlatformAuthBackend(),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
