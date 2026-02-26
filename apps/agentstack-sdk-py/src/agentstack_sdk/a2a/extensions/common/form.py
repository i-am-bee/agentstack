# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Generator
from typing import Generic, Literal, TypeVar

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


class CheckboxGroupField(BaseField):
    type: Literal["checkbox_group"] = "checkbox_group"
    fields: list[CheckboxField]


FormField = (
    TextField | DateField | FileField | SingleSelectField | MultiSelectField | CheckboxField | CheckboxGroupField
)

SettingsFormField = CheckboxGroupField | SingleSelectField


F = TypeVar("F", bound=FormField | SettingsFormField)


class BaseFormRender(BaseModel, Generic[F]):
    title: str | None = None
    description: str | None = None
    columns: int | None = Field(default=None, ge=1, le=4)
    submit_label: str | None = None
    fields: list[F]


class FormRender(BaseFormRender[FormField]):
    pass


class SettingsFormRender(BaseFormRender[SettingsFormField]):
    """FormRender for settings - only allows fields defined in SettingsFormField."""

    pass


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


class CheckboxGroupFieldValue(BaseModel):
    type: Literal["checkbox_group"] = "checkbox_group"
    value: dict[str, bool | None] | None = None


FormFieldValue = (
    TextFieldValue
    | DateFieldValue
    | FileFieldValue
    | SingleSelectFieldValue
    | MultiSelectFieldValue
    | CheckboxFieldValue
    | CheckboxGroupFieldValue
)

SettingsFormFieldValue = CheckboxGroupFieldValue | SingleSelectFieldValue

FV = TypeVar("FV", bound=FormFieldValue | SettingsFormFieldValue)


NonFileIterValue = dict[str, bool | None] | list[str] | str | bool | None
IterValue = list[dict[str, str | None]] | NonFileIterValue


class BaseFormResponse(BaseModel, Generic[FV]):
    values: dict[str, FV]

    def __iter__(
        self,
    ) -> Generator[tuple[str, IterValue]]:
        for key, value in self.values.items():
            match value:
                case FileFieldValue():
                    yield (
                        key,
                        [file.model_dump() for file in value.value] if value.value else None,
                    )
                case _:
                    yield key, value.value  # pyrefly: ignore[invalid-yield]


class FormResponse(BaseFormResponse[FormFieldValue]):
    pass


class SettingsFormResponse(BaseFormResponse[SettingsFormFieldValue]):
    """FormResponse for settings - only allows fields defined in SettingsFormFieldValue."""

    pass
