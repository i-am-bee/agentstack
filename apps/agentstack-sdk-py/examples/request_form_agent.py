# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from a2a.types import Message
from pydantic import BaseModel

from agentstack_sdk.a2a.extensions.common.form import FormRender, TextField
from agentstack_sdk.a2a.extensions.ui.request_form import RequestFormExtensionServer, RequestFormExtensionSpec
from agentstack_sdk.server import Server

server = Server()


class UserInfo(BaseModel):
    name: str | None

@server.agent()
async def request_form_agent(
    _message: Message,
    request_form: Annotated[
        RequestFormExtensionServer,
        RequestFormExtensionSpec(),
    ],
):
    """Request form agent"""
    user_info = await request_form.request_form(
        form=FormRender(
            title="What is your name?",
            fields=[TextField(id="name", label="Name", type="text", col_span=1)],
        ),
        model=UserInfo
    )
    yield f"Your name is {user_info.name}"


if __name__ == "__main__":
    server.run()
