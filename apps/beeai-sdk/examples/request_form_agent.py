# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from a2a.types import Message

from beeai_sdk.a2a.extensions.ui.form import FormExtensionServer, FormExtensionSpec, FormRender, TextField
from beeai_sdk.server import Server

server = Server()


@server.agent()
async def request_form_agent(
    message: Message,
    form: Annotated[
        FormExtensionServer,
        FormExtensionSpec(
            params=FormRender(
                id="initial_form",
                title="How are you?",
                fields=[TextField(id="mood", label="Mood", type="text", col_span=1)],
            )
        ),
    ],
):
    """Request form data"""
    try:
        form_data = await form.request_form(
            form=FormRender(
                id="form",
                title="Whats your name?",
                columns=2,
                fields=[
                    TextField(id="first_name", label="First Name", col_span=1),
                    TextField(id="last_name", label="Last Name", col_span=1),
                ],
            )
        )

        yield f"Hello {form_data.values['first_name'].value} {form_data.values['last_name'].value}"
    except ValueError:
        yield "Sorry, but I can't continue without knowing your name."


if __name__ == "__main__":
    server.run()
