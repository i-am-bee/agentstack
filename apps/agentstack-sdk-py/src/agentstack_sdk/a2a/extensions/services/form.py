# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Self, TypedDict, TypeVar, cast

from pydantic import BaseModel, TypeAdapter

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.extensions.common.form import FormRender, FormResponse


class FormDemands(TypedDict):
    initial_form: FormRender | None
    # TODO: We can put settings here too


class FormServiceExtensionMetadata(BaseModel):
    form_fulfillments: dict[str, FormResponse] = {}


class FormServiceExtensionParams(BaseModel):
    form_demands: FormDemands


class FormServiceExtensionSpec(BaseExtensionSpec[FormServiceExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/form/v1"

    @classmethod
    def demand(cls, initial_form: FormRender | None) -> Self:
        return cls(params=FormServiceExtensionParams(form_demands={"initial_form": initial_form}))


T = TypeVar("T")


class FormServiceExtensionServer(BaseExtensionServer[FormServiceExtensionSpec, FormServiceExtensionMetadata]):
    def parse_initial_form(self, *, model: type[T] = FormResponse) -> T | None:
        if self.data is None:
            return None

        intial_form = self.data.form_fulfillments["initial_form"]

        if intial_form is None:
            return None
        if model is FormResponse:
            return cast(T, intial_form)
        return TypeAdapter(model).validate_python(dict(intial_form))


class FormServiceExtensionClient(BaseExtensionClient[FormServiceExtensionSpec, FormRender]): ...
