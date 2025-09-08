# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncGenerator
from typing import Annotated

from a2a.types import Message

from beeai_sdk.a2a.extensions.ui.settings import (
    CheckboxField,
    SettingsExtensionServer,
    SettingsExtensionSpec,
    SettingsRender,
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
                    CheckboxField(
                        id="terms_and_conditions",
                        label="Do you agree with terms and conditions?",
                        type="checkbox",
                        default_value=False,
                    )
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
    if parsed_settings.values["terms_and_conditions"].value:
        yield "You agree with terms and conditions"
    else:
        yield "You don't agree with terms and conditions"


if __name__ == "__main__":
    server.run()
