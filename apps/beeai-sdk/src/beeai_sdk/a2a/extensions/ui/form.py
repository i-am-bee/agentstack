# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Literal

from a2a.types import Message as A2AMessage
from pydantic import BaseModel, Field

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from beeai_sdk.a2a.types import AgentMessage, InputRequired


class BaseField(BaseModel):
    id: str
    label: str
    required: bool | None = None
    col_span: int | None = Field(default=None, ge=1, le=4)


class TextField(BaseField):
    type: Literal["text"]
    placeholder: str | None = None
    default_value: str | None = None

    type: Literal["text"]
    value: str | None = None


class DateField(BaseField):
    type: Literal["date"]
    placeholder: str | None = None
    default_value: str | None = None


class FileItem(BaseModel):
    uri: str
    name: str | None = None
    mime_type: str | None = None


class FileField(BaseField):
    type: Literal["file"]
    accept: list[str]


class OptionItem(BaseModel):
    id: str
    label: str


class MultiSelectField(BaseField):
    type: Literal["multiselect"]
    options: list[OptionItem]
    default_value: list[str] | None = None


class CheckboxField(BaseField):
    type: Literal["checkbox"]
    content: str
    default_value: bool | None = None


FormField = TextField | DateField | FileField | MultiSelectField | CheckboxField


class FormRender(BaseModel):
    id: str
    title: str | None = None
    description: str | None = None
    columns: int | None = Field(default=None, ge=1, le=4)
    submit_label: str | None = None
    fields: list[FormField]


class TextFieldValue(BaseModel):
    type: str = "text"
    value: str | None = None


class DateFieldValue(BaseModel):
    type: str = "date"
    value: str | None = None


class FileInfo(BaseModel):
    uri: str
    name: str | None = None
    mime_type: str | None = None


class FileFieldValue(BaseModel):
    type: str = "file"
    value: list[FileInfo] | None = None


class MultiSelectFieldValue(BaseModel):
    type: str = "multiselect"
    value: list[str] | None = None


class CheckboxFieldValue(BaseModel):
    type: str = "checkbox"
    value: bool | None = None


FormFieldValue = TextFieldValue | DateFieldValue | FileFieldValue | MultiSelectFieldValue | CheckboxFieldValue


class FormResponse(BaseModel):
    id: str
    values: dict[str, FormFieldValue]


class FormExtensionSpec(BaseExtensionSpec[FormRender | None]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/form/v1"


class FormExtensionServer(BaseExtensionServer[FormExtensionSpec, FormResponse]):
    def request_form(self, *, form: FormRender):
        return InputRequired(message=AgentMessage(text=form.title, metadata={self.spec.URI: form}))

    def parse_form_response(self, *, message: A2AMessage):
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Form data has not been provided in response.")
        return FormResponse.model_validate(data)


class FormExtensionClient(BaseExtensionClient[FormExtensionSpec, FormRender]): ...
