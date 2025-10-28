# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message

from beeai_sdk.a2a.extensions.ui.settings import (
    CheckboxField,
    CheckboxGroupField,
    OptionItem,
    SettingsExtensionServer,
    SettingsExtensionSpec,
    SettingsRender,
    SingleSelectField,
)
from beeai_sdk.a2a.types import RunYield
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext

server = Server()


@server.agent()
async def settings_agent(
    message: Message,
    context: RunContext,
    settings: Annotated[
        SettingsExtensionServer,
        SettingsExtensionSpec(
            params=SettingsRender(
                fields=[
                    CheckboxGroupField(
                        id="thinking",
                        fields=[
                            CheckboxField(
                                id="thinking",
                                label="Thinking",
                                default_value=True,
                            )
                        ],
                    ),
                    SingleSelectField(
                        id="response_style",
                        label="Response Style",
                        options=[
                            OptionItem(value="concise", label="Concise"),
                            OptionItem(value="detailed", label="Detailed"),
                            OptionItem(value="humorous", label="Humorous"),
                        ],
                        default_value="concise",
                    ),
                ],
            ),
        ),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Demonstrate settings extension"""

    if not settings:
        yield "Settings extension hasn't been activated, no settings are available"
        return

    parsed_settings = settings.parse_settings_response()

    thinking_field = parsed_settings.values["thinking"]
    if thinking_field.type == "checkbox_group":
        if thinking_field.values["thinking"].value:
            yield "Thinking is enabled\n"
        else:
            yield "Thinking is disabled\n"


if __name__ == "__main__":
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
