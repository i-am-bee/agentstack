# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar, cast

from a2a.types import Message as A2AMessage
from pydantic import BaseModel, Field, TypeAdapter, model_validator

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.types import AgentMessage, InputRequired

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext


class BaseField(BaseModel):
    id: str
    label: str
    required: bool = False
    col_span: int | None = Field(default=None, ge=1, le=4)


class TextField(BaseField):
    type: Literal["text"] = "text"
    placeholder: str | None = None
    default_value: str | None = None
    auto_resize: bool | None = True


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


class SingleSelectField(BaseField):
    type: Literal["singleselect"] = "singleselect"
    options: list[OptionItem]
    default_value: str | None = None

    @model_validator(mode="after")
    def default_value_validator(self):
        if self.default_value:
            valid_values = {opt.id for opt in self.options}
            if self.default_value not in valid_values:
                raise ValueError(f"Invalid default_value: {self.default_value}. Must be one of {valid_values}")
        return self


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


FormField = TextField | DateField | FileField | SingleSelectField | MultiSelectField | CheckboxField


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


class SingleSelectFieldValue(BaseModel):
    type: Literal["singleselect"] = "singleselect"
    value: str | None = None


class MultiSelectFieldValue(BaseModel):
    type: Literal["multiselect"] = "multiselect"
    value: list[str] | None = None


class CheckboxFieldValue(BaseModel):
    type: Literal["checkbox"] = "checkbox"
    value: bool | None = None


FormFieldValue = (
    TextFieldValue
    | DateFieldValue
    | FileFieldValue
    | SingleSelectFieldValue
    | MultiSelectFieldValue
    | CheckboxFieldValue
)


class FormResponse(BaseModel):
    id: str
    values: dict[str, FormFieldValue]

    def __iter__(self):
        for key, value in self.values.items():
            match value:
                case FileFieldValue():
                    yield (
                        key,
                        [file.model_dump() for file in value.value] if value.value else None,
                    )
                case _:
                    yield key, value.value


class FormExtensionSpec(BaseExtensionSpec[FormRender | None]):
    URI: str = "https://a2a-extensions.agentstack.dev/ui/form/v1"


T = TypeVar("T")


class FormExtensionServer(BaseExtensionServer[FormExtensionSpec, FormResponse]):
    context: RunContext

    def handle_incoming_message(self, message: A2AMessage, context: RunContext):
        super().handle_incoming_message(message, context)
        self.context = context

    async def request_form(self, *, form: FormRender, model: type[T] = FormResponse) -> T | None:
        message = await self.context.yield_async(
            InputRequired(message=AgentMessage(text=form.title, metadata={self.spec.URI: form}))
        )
        return self.parse_form_response(message=message, model=model) if message else None

    def parse_form_response(self, *, message: A2AMessage, model: type[T] = FormResponse) -> T | None:
        form_response = self.parse_client_metadata(message)
        if form_response is None:
            return None
        if model is FormResponse:
            return cast(T, form_response)
        return TypeAdapter(model).validate_python(dict(form_response))


class FormExtensionClient(BaseExtensionClient[FormExtensionSpec, FormRender]): ...
