# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

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
                    CheckboxGroupField(
                        id="tools",
                        fields=[
                            CheckboxField(
                                id="tool_1",
                                label="Tool 1",
                                default_value=True,
                            ),
                            CheckboxField(
                                id="tool_2",
                                label="Tool 2",
                                default_value=False,
                            ),
                            CheckboxField(
                                id="tool_3",
                                label="Tool 3",
                                default_value=True,
                            ),
                        ],
                    ),
                    SingleSelectField(
                        id="length",
                        options=[
                            OptionItem(
                                label="Short",
                                value="short",
                            ),
                            OptionItem(
                                label="Medium",
                                value="medium",
                            ),
                            OptionItem(
                                label="Long",
                                value="long",
                            ),
                        ],
                        default_value="short",
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

    tools_field = parsed_settings.values["tools"]
    if tools_field.type == "checkbox_group":
        if tools_field.values["tool_1"].value:
            yield "Tool 1 is enabled\n"
        else:
            yield "Tool 1 is disabled\n"
        if tools_field.values["tool_2"].value:
            yield "Tool 2 is enabled\n"
        else:
            yield "Tool 2 is disabled\n"
        if tools_field.values["tool_3"].value:
            yield "Tool 3 is enabled\n"
        else:
            yield "Tool 3 is disabled\n"

    length_field = parsed_settings.values["length"]
    if length_field.type == "single_select":
        yield f"Length is {length_field.value}\n"


if __name__ == "__main__":
    server.run()
