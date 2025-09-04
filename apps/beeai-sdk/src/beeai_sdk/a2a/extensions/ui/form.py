# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2a.types import Message as A2AMessage
from pydantic import BaseModel, Field, model_validator

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from beeai_sdk.a2a.types import AgentMessage, InputRequired

if TYPE_CHECKING:
    from beeai_sdk.server.context import RunContext


class BaseField(BaseModel):
    id: str
    label: str
    required: bool = False
    col_span: int | None = Field(default=None, ge=1, le=4)


class TextField(BaseField):
    type: Literal["text"] = "text"
    placeholder: str | None = None
    default_value: str | None = None


class DateField(BaseField):
    type: Literal["date"] = "date"
    placeholder: str | None = None
    default_value: str | None = None


class FileItem(BaseModel):
    uri: str
    name: str | None = None
    mime_type: str | None = None


class FileField(BaseField):
    type: Literal["file"] = "file"
    accept: list[str]


class OptionItem(BaseModel):
    id: str
    label: str


class MultiSelectField(BaseField):
    type: Literal["multiselect"] = "multiselect"
    options: list[OptionItem]
    default_value: list[str] | None = None

    @model_validator(mode="after")
    def default_values_validator(self):
        if self.default_value:
            valid_values = {opt.id for opt in self.options}
            invalid_values = [v for v in self.default_value if v not in valid_values]
            if invalid_values:
                raise ValueError(f"Invalid default_value(s): {invalid_values}. Must be one of {valid_values}")
        return self


class CheckboxField(BaseField):
    type: Literal["checkbox"] = "checkbox"
    content: str
    default_value: bool = False


FormField = TextField | DateField | FileField | MultiSelectField | CheckboxField


class FormRender(BaseModel):
    id: str
    title: str | None = None
    description: str | None = None
    columns: int | None = Field(default=None, ge=1, le=4)
    submit_label: str | None = None
    fields: list[FormField]


class TextFieldValue(BaseModel):
    type: Literal["text"] = "text"
    value: str | None = None


class DateFieldValue(BaseModel):
    type: Literal["date"] = "date"
    value: str | None = None


class FileInfo(BaseModel):
    uri: str
    name: str | None = None
    mime_type: str | None = None


class FileFieldValue(BaseModel):
    type: Literal["file"] = "file"
    value: list[FileInfo] | None = None


class MultiSelectFieldValue(BaseModel):
    type: Literal["multiselect"] = "multiselect"
    value: list[str] | None = None


class CheckboxFieldValue(BaseModel):
    type: Literal["checkbox"] = "checkbox"
    value: bool | None = None


FormFieldValue = TextFieldValue | DateFieldValue | FileFieldValue | MultiSelectFieldValue | CheckboxFieldValue


class FormResponse(BaseModel):
    id: str
    values: dict[str, FormFieldValue]


class FormExtensionSpec(BaseExtensionSpec[FormRender | None]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/form/v1"


class FormExtensionServer(BaseExtensionServer[FormExtensionSpec, FormResponse]):
    def handle_incoming_message(self, message: A2AMessage, context: RunContext):
        super().handle_incoming_message(message, context)
        self.context = context

    async def request_form(self, *, form: FormRender) -> FormResponse:
        resume = await self.context.yield_async(
            InputRequired(message=AgentMessage(text=form.title, metadata={self.spec.URI: form}))
        )
        if isinstance(resume, A2AMessage):
            return self.parse_form_response(message=resume)
        else:
            raise ValueError("Form data has not been provided in response.")

    def parse_form_response(self, *, message: A2AMessage):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Form data has not been provided in response.")
        return FormResponse.model_validate(data)


class FormExtensionClient(BaseExtensionClient[FormExtensionSpec, FormRender]): ...
