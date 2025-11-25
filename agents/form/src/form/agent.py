# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Annotated
from pydantic import BaseModel

import a2a.types
from a2a.types import Message


from agentstack_sdk.server import Server

import agentstack_sdk.a2a.extensions
from agentstack_sdk.a2a.extensions.common.form import (
    DateField,
    TextField,
    FileField,
    FileInfo,
    CheckboxField,
    MultiSelectField,
    OptionItem,
    FormRender,
)
from agentstack_sdk.a2a.extensions.services.form import (
    FormServiceExtensionServer,
    FormServiceExtensionSpec,
)

agent_detail_extension_spec = agentstack_sdk.a2a.extensions.AgentDetailExtensionSpec(
    params=agentstack_sdk.a2a.extensions.AgentDetail(
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
    title="Let’s go on an adventure",
    columns=2,
    fields=[location, date_from, date_to, notes, flexible, interests],
)
form_extension_spec = FormServiceExtensionSpec.demand(initial_form=form_render)

server = Server()


class FormData(BaseModel):
    location: str | None
    date_from: str | None
    date_to: str | None
    notes: list[FileInfo] | None
    flexible: bool | None
    interests: list[str] | None


@server.agent(
    name="Single-turn Form Agent",
    documentation_url=f"https://github.com/i-am-bee/agentstack/blob/{os.getenv('RELEASE_VERSION', 'main')}/agents/form",
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
    _message: Message,
    form: Annotated[
        FormServiceExtensionServer,
        form_extension_spec,
    ],
):
    """Example demonstrating a single-turn agent using a form to collect user input."""

    form_data = form.parse_initial_form(model=FormData)

    yield f"Hello {form_data.location}"


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
