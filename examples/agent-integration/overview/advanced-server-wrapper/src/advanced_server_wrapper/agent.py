# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.common.form import FormRender, TextField
from agentstack_sdk.a2a.extensions.ui.form_request import (
    FormRequestExtensionServer,
    FormRequestExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from pydantic import BaseModel

server = Server()


class UserDetails(BaseModel):
    name: str | None
    email: str | None


@server.agent()
async def advanced_server_wrapper_example(
    input: Message, context: RunContext, form_request: Annotated[FormRequestExtensionServer, FormRequestExtensionSpec()]
):
    """Agent that pauses execution to request user input"""
    yield AgentMessage(text="I need some information from you.")

    # Execution pauses here - task enters input_required state
    # User fills out the form in the UI
    form_data = await form_request.request_form(
        form=FormRender(
            title="Please provide your details",
            fields=[
                TextField(id="name", label="Your Name"),
                TextField(id="email", label="Email Address"),
            ],
        ),
        model=UserDetails,
    )

    # Execution resumes after user submits the form
    if form_data:
        yield AgentMessage(text=f"Thank you, {form_data.name}! I'll contact you at {form_data.email}.")
    else:
        yield AgentMessage(text="Form was not filled out.")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
