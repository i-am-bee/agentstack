# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import deprecated

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.CheckboxField instead")
class CheckboxField(BaseModel):
    id: str
    label: str
    default_value: bool = False


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.CheckboxGroupField instead")
class CheckboxGroupField(BaseModel):
    id: str
    type: Literal["checkbox_group"] = "checkbox_group"
    fields: list[CheckboxField]


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.OptionItem instead (note: uses 'id' instead of 'value')")
class OptionItem(BaseModel):
    label: str
    value: str


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.SingleSelectField instead (note: type is 'singleselect')")
class SingleSelectField(BaseModel):
    type: Literal["single_select"] = "single_select"
    id: str
    label: str
    options: list[OptionItem]
    default_value: str


@deprecated("Use FormServiceExtensionSpec.demand_settings() with SettingsFormRender instead")
class SettingsRender(BaseModel):
    fields: list[Annotated[CheckboxGroupField | SingleSelectField, Field(discriminator="type")]]


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.CheckboxFieldValue instead")
class CheckboxFieldValue(BaseModel):
    value: bool | None = None


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.CheckboxGroupFieldValue instead")
class CheckboxGroupFieldValue(BaseModel):
    type: Literal["checkbox_group"] = "checkbox_group"
    values: dict[str, CheckboxFieldValue]


@deprecated("Use agentstack_sdk.a2a.extensions.common.form.SingleSelectFieldValue instead")
class SingleSelectFieldValue(BaseModel):
    type: Literal["single_select"] = "single_select"
    value: str | None = None


SettingsFieldValue = CheckboxGroupFieldValue | SingleSelectFieldValue


@deprecated("Use FormServiceExtensionServer.parse_settings_form() with SettingsFormResponse instead")
class AgentRunSettings(BaseModel):
    values: dict[str, SettingsFieldValue]


@deprecated("Use FormServiceExtensionSpec.demand_settings() instead")
class SettingsExtensionSpec(BaseExtensionSpec[SettingsRender | None]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/ui/settings/v1"


@deprecated("Use FormServiceExtensionServer.parse_settings_form() instead")
class SettingsExtensionServer(BaseExtensionServer[SettingsExtensionSpec, AgentRunSettings]):
    @deprecated("Use FormServiceExtensionServer.parse_settings_form() instead")
    def parse_settings_response(self) -> AgentRunSettings:
        return AgentRunSettings.model_validate(self._metadata_from_client)


@deprecated("Use FormServiceExtensionClient instead")
class SettingsExtensionClient(BaseExtensionClient[SettingsExtensionSpec, SettingsRender]): ...
