# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from a2a.utils.message import get_message_text
from agentstack_sdk.a2a.extensions.common.form import FormRender, TextField
from agentstack_sdk.a2a.extensions.ui.form_request import (
    FormRequestExtensionServer,
    FormRequestExtensionSpec,
)
from agentstack_sdk.server import Server
from pydantic import BaseModel

server = Server()


class ContactInfo(BaseModel):
    email: str | None
    phone: str | None
    company: str | None


@server.agent()
async def dynamic_form_requests_example(
    message: Message,
    form_request: Annotated[
        FormRequestExtensionServer,
        FormRequestExtensionSpec(),
    ],
):
    """Agent that requests forms dynamically during conversation"""

    user_input = get_message_text(message)

    # Check if user wants to provide contact information
    if "contact" in user_input.lower() or "reach" in user_input.lower():
        # Request contact form dynamically
        contact_info = await form_request.request_form(
            form=FormRender(
                title="Please provide your contact information",
                columns=2,
                fields=[
                    TextField(id="email", label="Email Address", col_span=2),
                    TextField(id="phone", label="Phone Number", col_span=1),
                    TextField(id="company", label="Company", col_span=1),
                ],
            ),
            model=ContactInfo,
        )

        if contact_info is None:
            yield "No contact information received."
        else:
            yield f"Thank you! I'll contact you at {contact_info.email} or {contact_info.phone} regarding {contact_info.company}."
    else:
        yield "Hello! If you'd like me to contact you, just let me know and I'll ask for your details."


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    run()
