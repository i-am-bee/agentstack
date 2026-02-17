# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.ui.settings import (
    CheckboxField,
    CheckboxGroupField,
    CheckboxGroupFieldValue,
    SettingsExtensionServer,
    SettingsExtensionSpec,
    SettingsRender,
)
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def basic_settings_example(
    message: Message,
    context: RunContext,
    settings: Annotated[
        SettingsExtensionServer,
        SettingsExtensionSpec(
            params=SettingsRender(
                fields=[
                    CheckboxGroupField(
                        id="thinking_group",
                        fields=[
                            CheckboxField(
                                id="thinking",
                                label="Enable Thinking Mode",
                                default_value=True,
                            )
                        ],
                    )
                ],
            ),
        ),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Agent that demonstrates settings configuration"""

    if not settings:
        yield "Settings extension hasn't been activated, no settings are available"
        return

    parsed_settings = settings.parse_settings_response()

    thinking_group = parsed_settings.values["thinking_group"]
    if isinstance(thinking_group, CheckboxGroupFieldValue):
        if thinking_group.values["thinking"].value:
            yield "Thinking mode is enabled - I'll show my reasoning process.\n"
        else:
            yield "Thinking mode is disabled - I'll provide direct responses.\n"


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
