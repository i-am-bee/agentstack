# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio

from a2a.types import Message, Part, Role, TextPart

from beeai_sdk.platform import PlatformClient, Provider


async def run(base_url: str = "http://127.0.0.1:8333"):
    async with PlatformClient(base_url=base_url) as client:
        providers = await Provider.list(client=client)
        if not providers:
            print("No providers found")

        provider = providers[0]
        print(f"Sending message to provider {provider.agent_card.name}")
        async with provider.a2a_client(client=client) as a2a_client:
            async for event in a2a_client.send_message(
                Message(role=Role.user, message_id="test", parts=[Part(TextPart(text="Howdy!"))])
            ):
                print(event)


if __name__ == "__main__":
    asyncio.run(run())
