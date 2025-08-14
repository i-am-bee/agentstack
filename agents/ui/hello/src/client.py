# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    TaskStatusUpdateEvent,
    SendStreamingMessageSuccessResponse,
    Message,
)
from pydantic import BaseModel


class MessagePart(BaseModel):
    content: str


class BeeAIMessage(BaseModel):
    parts: list[MessagePart]


def message_to_beeai_message(
    message: SendStreamingMessageSuccessResponse,
) -> BeeAIMessage | None:
    if isinstance(message.result, TaskStatusUpdateEvent):
        if message.result.status.message is not None:
            return BeeAIMessage(
                parts=[
                    MessagePart(content=part.root.text)
                    for part in message.result.status.message.parts
                ]
            )
    return None


async def run_stream() -> AsyncGenerator[str, str]:
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url="http://localhost:8000",
        )

        card = await resolver.get_agent_card()
        client = A2AClient(httpx_client, agent_card=card)

        # TODO not working after a2a 0.3.0 update
        result_generator = client.send_message(
            Message.model_validate(
                {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "How are you??"}],
                    "messageId": "bazbar",
                }
            )
        )
        async for result in result_generator:
            print(result)
            yield ""
            # beeai_message = message_to_beeai_message(result.root)
            # if (beeai_message is not None):
            #     yield beeai_message


async def main():
    async for event in run_stream():
        print(event)
        # print(event.model_dump_json(indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
