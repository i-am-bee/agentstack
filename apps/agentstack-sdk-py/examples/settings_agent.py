# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions.common.form import (
    CheckboxField,
    CheckboxGroupField,
    OptionItem,
    SettingsFormRender,
    SingleSelectField,
)
from agentstack_sdk.a2a.extensions.services.form import (
    FormServiceExtensionServer,
    FormServiceExtensionSpec,
)
from agentstack_sdk.a2a.types import RunYield
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext

server = Server()


@server.agent()
async def settings_agent(
    message: Message,
    context: RunContext,
    form: Annotated[
        FormServiceExtensionServer,
        FormServiceExtensionSpec.demand_settings(
            settings_form=SettingsFormRender(
                fields=[
                    CheckboxGroupField(
                        id="thinking",
                        label="Thinking Options",
                        fields=[
                            CheckboxField(
                                id="thinking",
                                label="Enable Thinking",
                                content="Show agent's reasoning process",
                                default_value=True,
                            )
                        ],
                    ),
                    SingleSelectField(
                        id="response_style",
                        label="Response Style",
                        options=[
                            OptionItem(id="concise", label="Concise"),
                            OptionItem(id="detailed", label="Detailed"),
                            OptionItem(id="humorous", label="Humorous"),
                        ],
                        default_value="concise",
                    ),
                ],
            )
        ),
    ],
) -> AsyncGenerator[RunYield, Message]:
    """Demonstrate settings form extension"""

    if not form:
        yield "Form extension hasn't been activated, no settings are available"
        return

    parsed_settings = form.parse_settings_form()

    if not parsed_settings:
        yield "No settings provided"
        return

    thinking_field = parsed_settings.values.get("thinking")
    if thinking_field and thinking_field.type == "checkbox_group":
        thinking_enabled = thinking_field.value and thinking_field.value.get("thinking", False)
        if thinking_enabled:
            yield "Thinking is enabled\n"
        else:
            yield "Thinking is disabled\n"

    response_style_field = parsed_settings.values.get("response_style")
    if response_style_field and response_style_field.type == "singleselect":
        yield f"Response style: {response_style_field.value}\n"


if __name__ == "__main__":
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
