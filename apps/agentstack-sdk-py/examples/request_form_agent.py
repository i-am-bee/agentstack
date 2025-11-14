# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from a2a.types import Message
from pydantic import BaseModel

from agentstack_sdk.a2a.extensions.common.form import (
    CheckboxField,
    DateField,
    FileField,
    FileInfo,
    FormRender,
    MultiSelectField,
    OptionItem,
    SingleSelectField,
    TextField,
)
from agentstack_sdk.a2a.extensions.ui.request_form import RequestFormExtensionServer, RequestFormExtensionSpec
from agentstack_sdk.server import Server

server = Server()


class KitchenSink(BaseModel):
    text_field: str | None
    date_field: str | None
    file_field: list[FileInfo] | None
    singleselect_field: str | None
    multiselect_field: list[str] | None
    checkbox_field: bool | None


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
            title="Kitchen Sink Form",
            columns=2,
            fields=[
                TextField(id="text_field", label="Text Field", col_span=1),
                DateField(id="date_field", label="Date Field", col_span=1),
                FileField(id="file_field", label="File Field", accept=["*/*"], col_span=2),
                SingleSelectField(
                    id="singleselect_field",
                    label="Single-Select Field",
                    options=[
                        OptionItem(id="option1", label="Option 1"),
                        OptionItem(id="option2", label="Option 2"),
                    ],
                    col_span=2,
                ),
                MultiSelectField(
                    id="multiselect_field",
                    label="Multi-Select Field",
                    options=[
                        OptionItem(id="option1", label="Option 1"),
                        OptionItem(id="option2", label="Option 2"),
                    ],
                    col_span=2,
                ),
                CheckboxField(
                    id="checkbox_field",
                    label="Checkbox Field",
                    content="I agree to the terms and conditions.",
                    col_span=2,
                ),
            ],
        ),
        model=KitchenSink,
    )
    if user_info is None:
        yield "No user info received."
    else:
        yield user_info.model_dump_json()


if __name__ == "__main__":
    server.run()
