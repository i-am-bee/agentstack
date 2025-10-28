# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from a2a.types import Message

from beeai_sdk.a2a.extensions.ui.form import (
    CheckboxField,
    DateField,
    FileField,
    FormExtensionServer,
    FormExtensionSpec,
    FormRender,
    MultiSelectField,
    OptionItem,
    SingleSelectField,
    TextField,
)
from beeai_sdk.server import Server

server = Server()


@server.agent()
async def request_form_agent(
    _message: Message,
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
                id="all_fields_form",
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
            )
        )

        if form_data is None:
            yield "No form data received."
            return

        response = "Form data received:\n"
        for field_id, field_value in form_data.values.items():
            response += f"- {field_id}: {field_value.value}\n"
        yield response

    except ValueError:
        yield "Sorry, but I can't continue without receiving the form data."


if __name__ == "__main__":
    server.run()
