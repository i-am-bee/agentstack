# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from a2a.types import Message

from agentstack_sdk.a2a.extensions.common.form import FormRender, TextField
from agentstack_sdk.a2a.extensions.services.form import (
    FormServiceExtensionServer,
    FormServiceExtensionSpec,
)
from agentstack_sdk.server import Server

server = Server()


@server.agent()
async def form_agent(
    _message: Message,
    form: Annotated[
        FormServiceExtensionServer,
        FormServiceExtensionSpec.demand(
            initial_form=FormRender(
                title="How are you?",
                fields=[TextField(id="mood", label="Mood", type="text", col_span=1)],
            )
        ),
    ],
):
    """Initial form agent"""
    if form.data.form_fulfillments["initial_form"]:
        yield f"Your mood is {form.data.form_fulfillments['initial_form'].values['mood'].value}"
    else:
        yield "No form data received."


if __name__ == "__main__":
    server.run()
