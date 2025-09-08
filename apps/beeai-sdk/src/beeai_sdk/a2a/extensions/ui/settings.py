# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


class BaseField(BaseModel):
    id: str
    label: str


class CheckboxField(BaseField):
    type: Literal["checkbox"] = "checkbox"
    default_value: bool = False


class SettingsRender(BaseModel):
    fields: list[CheckboxField]


class CheckboxFieldValue(BaseModel):
    type: Literal["checkbox"] = "checkbox"
    value: bool | None = None


SettingsFieldValue = CheckboxFieldValue


class AgentRunSettings(BaseModel):
    values: dict[str, SettingsFieldValue]


class SettingsExtensionSpec(BaseExtensionSpec[SettingsRender | None]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/settings/v1"


class SettingsExtensionServer(BaseExtensionServer[SettingsExtensionSpec, AgentRunSettings]):
    def parse_settings_response(self) -> AgentRunSettings:
        return AgentRunSettings.model_validate(self._metadata_from_client)


class SettingsExtensionClient(BaseExtensionClient[SettingsExtensionSpec, SettingsRender]): ...
