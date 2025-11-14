# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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
