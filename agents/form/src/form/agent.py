# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated


import a2a.server.agent_execution
import a2a.server.apps
import a2a.server.events
import a2a.server.request_handlers
import a2a.server.tasks
from a2a.types import (
    Message,
)

from a2a.utils.message import get_message_text

from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext

import beeai_sdk.a2a.extensions
from beeai_sdk.a2a.extensions.ui.form import (
    DateField,
    TextField,
    FileField,
    CheckboxField,
    MultiSelectField,
    OptionItem,
    FormExtensionServer,
    FormExtensionSpec,
    FormRender,
)

agent_detail_extension_spec = beeai_sdk.a2a.extensions.AgentDetailExtensionSpec(
    params=beeai_sdk.a2a.extensions.AgentDetail(
        interaction_mode="multi-turn",
    )
)

location = TextField(type="text", id="location", label="Location", required=True, col_span=2)
date_from = DateField(type="date", id="date_from", label="Date from", required=False, col_span=1)
date_to = DateField(type="date", id="date_to", label="Date to", required=False, col_span=1)
flexible = CheckboxField(
    type="checkbox",
    id="flexible",
    label="Do you have flexibility with your travel dates?",
    content="Yes, I'm flexible",
    required=False,
    col_span=2,
)
notes = FileField(type="file", id="notes", label="Upload notes", accept=["text/*"], required=False, col_span=2)
interests = MultiSelectField(
    type="multiselect",
    id="interests",
    label="Interests",
    required=False,
    col_span=2,
    options=[
        OptionItem(id="cuisine", label="Cuisine"),
        OptionItem(id="nature", label="Nature"),
        OptionItem(id="photography", label="Photography"),
    ],
    default_value=["nature"],
)

form_render = FormRender(
    id="adventure_form",
    title="Let’s go on an adventure",
    columns=2,
    fields=[location, date_from, date_to, notes, flexible, interests],
)
form_extension_spec = FormExtensionSpec(form_render)

server = Server()


@server.agent(
    name="Single-turn Form Agent",
    documentation_url=f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/form",
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    capabilities=a2a.types.AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=False,
        extensions=[
            *form_extension_spec.to_agent_card_extensions(),
            *agent_detail_extension_spec.to_agent_card_extensions(),
        ],
    ),
    skills=[
        a2a.types.AgentSkill(
            id="form", name="Form", description="Answer complex questions using web search sources", tags=["form"]
        )
    ],
)
async def agent(
    input: Message,
    form: Annotated[
        FormExtensionServer,
        form_extension_spec,
    ],
):
    """Example demonstrating a single-turn agent using a form to collect user input."""

    form_data = form.parse_form_response(message=input)

    yield f"Hello {form_data.values['location'].value}"


def serve():
    try:
        server.run(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 10001)),
            configure_telemetry=True,
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()
