# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Any, Self, TypeVar

from pydantic import BaseModel, TypeAdapter
from typing_extensions import TypedDict

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.extensions.common.form import (
    FormRender,
    FormResponse,
    SettingsFormRender,
    SettingsFormResponse,
)


class FormDemands(TypedDict, total=False):
    initial_form: FormRender | None
    settings_form: SettingsFormRender | None


class FormServiceExtensionMetadata(BaseModel):
    form_fulfillments: dict[str, FormResponse | SettingsFormResponse] = {}


class FormServiceExtensionParams(BaseModel):
    form_demands: FormDemands


class FormServiceExtensionSpec(BaseExtensionSpec[FormServiceExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/form/v1"

    @classmethod
    def demand(cls, initial_form: FormRender | None) -> Self:
        """Create form extension demanding an initial_form."""
        return cls(params=FormServiceExtensionParams(form_demands={"initial_form": initial_form}))

    @classmethod
    def demand_settings(cls, settings_form: SettingsFormRender) -> Self:
        """
        Create form extension demanding a settings_form.

        This is the preferred way to add settings to an agent, replacing the deprecated SettingsExtensionSpec.
        """
        return cls(params=FormServiceExtensionParams(form_demands={"settings_form": settings_form}))

    @classmethod
    def demand_forms(
        cls, *, initial_form: FormRender | None = None, settings_form: SettingsFormRender | None = None
    ) -> Self:
        """Create form extension demanding both initial_form and settings_form."""
        return cls(
            params=FormServiceExtensionParams(
                form_demands={
                    "initial_form": initial_form,
                    "settings_form": settings_form,
                }
            )
        )


T = TypeVar("T")


class FormServiceExtensionServer(BaseExtensionServer[FormServiceExtensionSpec, FormServiceExtensionMetadata]):
    def parse_initial_form(self, *, model: type[T] | None = None) -> T | FormResponse | None:
        """Parse initial_form from form_fulfillments."""
        if self.data is None:
            return None

        initial_form = getattr(self.data, "form_fulfillments", {}).get("initial_form")
        return (
            TypeAdapter(model).validate_python(dict(initial_form))
            if initial_form is not None and model is not None
            else initial_form
        )

    def parse_settings_form(self, *, model: type[T] | None = None) -> T | SettingsFormResponse | None:
        """
        Parse settings_form from form_fulfillments.

        This is the preferred way to access settings in agents, replacing the
        deprecated SettingsExtensionServer.parse_settings_response().
        """
        if self.data is None:
            return None

        settings_form = getattr(self.data, "form_fulfillments", {}).get("settings_form")

        return (
            TypeAdapter(model).validate_python(dict(settings_form))
            if settings_form is not None and model is not None
            else settings_form
        )


class FormServiceExtensionClient(BaseExtensionClient[FormServiceExtensionSpec, FormRender]):
    def fulfillment_metadata(
        self, *, form_fulfillments: dict[str, FormResponse | SettingsFormResponse]
    ) -> dict[str, Any]:
        return {
            self.spec.URI: FormServiceExtensionMetadata(form_fulfillments=form_fulfillments).model_dump(mode="json")
        }
