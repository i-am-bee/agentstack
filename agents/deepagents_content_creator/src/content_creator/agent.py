# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions import (
    AgentDetail,
    AgentDetailContributor,
    LLMServiceExtensionServer,
    LLMServiceExtensionSpec,
)
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from agentstack_sdk.server.middleware.platform_auth_backend import PlatformAuthBackend

server = Server()


@server.agent(
    name="Content Writer Agent (Deepagents)",
    documentation_url=f"https://github.com/i-am-bee/agentstack/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/deepagents_content_creator",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],  # TODO: output is a text + cover image
    description="A content writer for a technology company that creates engaging, informative content that educates readers about AI, software development, and emerging technologies.",
    detail=AgentDetail(
        interaction_mode="multi-turn",
        author=AgentDetailContributor(name="IBM"),
    ),
)
async def deepagents_content_creator(
    message: Message,
    context: RunContext,
    llm: Annotated[LLMServiceExtensionServer, LLMServiceExtensionSpec.single_demand()],
):
    # TODO
    pass


def serve():
    try:
        server.run(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 10003)),
            configure_telemetry=True,
            auth_backend=PlatformAuthBackend(),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
