# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated

from a2a.types import Message
from agentstack_sdk.a2a.extensions.common.form import FormRender, TextField
from agentstack_sdk.a2a.extensions.services.form import (
    FormServiceExtensionServer,
    FormServiceExtensionSpec,
)
from agentstack_sdk.server import Server
from pydantic import BaseModel

server = Server()

class UserInfo(BaseModel):
    first_name: str | None
    last_name: str | None

@server.agent()
async def initial_form_rendering_example(
    _message: Message,
    form: Annotated[
        FormServiceExtensionServer,
        FormServiceExtensionSpec.demand(
            initial_form=FormRender(
                title="Welcome! Please tell us about yourself",
                columns=2,
                fields=[
                    TextField(id="first_name", label="First Name", col_span=1),
                    TextField(id="last_name", label="Last Name", col_span=1),
                ],
            )
        ),
    ],
):
    """Agent that collects user information through an initial form"""
    
    # Parse the form data using a Pydantic model
    user_info = form.parse_initial_form(model=UserInfo)
    
    if user_info is None:
        yield "No form data received."
    else:
        yield f"Hello {user_info.first_name} {user_info.last_name}! Nice to meet you."


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    run()