# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


class CheckboxField(BaseModel):
    id: str
    label: str
    default_value: bool = False


class CheckboxGroupField(BaseModel):
    id: str
    type: Literal["checkbox_group"] = "checkbox_group"
    fields: list[CheckboxField]


class OptionItem(BaseModel):
    label: str
    value: str


class SingleSelectField(BaseModel):
    type: Literal["single_select"] = "single_select"
    id: str
    label: str
    options: list[OptionItem]
    default_value: str


class SettingsRender(BaseModel):
    fields: list[CheckboxGroupField | SingleSelectField]


class CheckboxFieldValue(BaseModel):
    value: bool | None = None


class CheckboxGroupFieldValue(BaseModel):
    type: Literal["checkbox_group"] = "checkbox_group"
    values: dict[str, CheckboxFieldValue]


class SingleSelectFieldValue(BaseModel):
    type: Literal["single_select"] = "single_select"
    value: str | None = None


SettingsFieldValue = CheckboxGroupFieldValue | SingleSelectFieldValue


class AgentRunSettings(BaseModel):
    values: dict[str, SettingsFieldValue]


class SettingsExtensionSpec(BaseExtensionSpec[SettingsRender | None]):
    URI: str = "https://a2a-extensions.agentstack.dev/ui/settings/v1"


class SettingsExtensionServer(BaseExtensionServer[SettingsExtensionSpec, AgentRunSettings]):
    def parse_settings_response(self) -> AgentRunSettings:
        return AgentRunSettings.model_validate(self._metadata_from_client)


class SettingsExtensionClient(BaseExtensionClient[SettingsExtensionSpec, SettingsRender]): ...
