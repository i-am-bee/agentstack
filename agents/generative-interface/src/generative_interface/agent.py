# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Annotated

from a2a.types import Message, TextPart
from agentstack_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from agentstack_sdk.a2a.extensions.services.generative_interface import (
    GenerativeInterfaceExtensionServer,
    GenerativeInterfaceExtensionSpec,
    GenerativeInterfaceSpec,
)
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.middleware.platform_auth_backend import PlatformAuthBackend
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

server = Server()

AGENT_GOAL = """You are a fortune teller, you need to first ask user whether they agree to know their fortune, otherwise reject. If agreed tell something funny."""


def _get_text(message: Message) -> str:
    return "\n\n".join(part.root.text for part in message.parts or [] if isinstance(part.root, TextPart))


@server.agent(
    name="Generative Interface Agent",
    documentation_url=f"https://github.com/i-am-bee/agentstack/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/generative-interface",
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    description="Financial advisor with dynamic UI generation",
    detail=AgentDetail(
        interaction_mode="multi-turn",
        author=AgentDetailContributor(name="IBM"),
    ),
)
async def agent(
    message: Message,
    context: RunContext,
    ui: Annotated[GenerativeInterfaceExtensionServer, GenerativeInterfaceExtensionSpec.demand()],
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
):
    await context.store(message)

    (llm_config,) = llm.data.llm_fulfillments.values()
    client = AsyncOpenAI(
        api_key=llm_config.api_key,
        base_url=llm_config.api_base,
    )

    system_prompt = f"""{ui.catalog_prompt}

You are a fortune teller, you need to first ask user whether they agree to know their fortune, otherwise reject. If agreed tell something funny
"""

    history = context.load_history()
    llm_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]

    async for item in history:
        if isinstance(item, Message):
            if content := _get_text(item):
                role = "assistant" if item.role == "agent" else "user"
                llm_messages.append({"role": role, "content": content})

    while True:
        response = await client.chat.completions.create(
            model=llm_config.api_model,
            messages=llm_messages,
        )

        assistant_content = response.choices[0].message.content or ""
        llm_messages.append({"role": "assistant", "content": assistant_content})

        generative_ui = parse_generative_ui(assistant_content)

        if not generative_ui:
            yield assistant_content
            break

        ui_response = await ui.request_ui(spec=generative_ui)
        if not ui_response:
            break

        user_response = f"User selected: {ui_response.component_id}"
        llm_messages.append({"role": "user", "content": user_response})


def parse_generative_ui(content: str) -> GenerativeInterfaceSpec | None:
    spec: dict = {"root": "", "elements": {}}

    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            patch = json.loads(line)
            if patch.get("op") == "set":
                path = patch.get("path", "")
                value = patch.get("value")
                if path == "/root":
                    spec["root"] = value
                elif path.startswith("/elements/"):
                    key = path[len("/elements/"):]
                    spec["elements"][key] = value
        except json.JSONDecodeError:
            continue

    if spec["root"] and spec["elements"]:
        return GenerativeInterfaceSpec.model_validate(spec)
    return None


def serve():
    try:
        server.run(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 10001)),
            configure_telemetry=True,
            auth_backend=PlatformAuthBackend(),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
