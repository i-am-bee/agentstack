# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions import (
    Citation,
    CitationExtensionServer,
    CitationExtensionSpec,
)
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def citation_basic_usage_example(
    input: Message, context: RunContext, citation: Annotated[CitationExtensionServer, CitationExtensionSpec()]
):
    response_text = "Python is the most popular programming language for AI development."

    citations = [
        Citation(
            url="https://survey.stackoverflow.com/2023",
            title="Stack Overflow Developer Survey 2023",
            description="Annual survey of developer preferences and trends",
            start_index=0,
            end_index=47,  # "Python is the most popular programming language"
        )
    ]

    yield citation.message(text=response_text, citations=citations)


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
