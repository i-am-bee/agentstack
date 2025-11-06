# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from typing import Self, TypedDict

import pydantic

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.extensions.common.form import FormRender, FormResponse


class FormDemands(TypedDict):
    initial_form: FormRender | None
    # TODO: We can put settings here too


class FormServiceExtensionMetadata(pydantic.BaseModel):
    form_fulfillments: dict[str, FormResponse] = {}


class FormServiceExtensionParams(pydantic.BaseModel):
    form_demands: FormDemands


class FormServiceExtensionSpec(BaseExtensionSpec[FormServiceExtensionParams]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/services/form/v1"

    @classmethod
    def demand(cls, initial_form: FormRender | None) -> Self:
        return cls(
            params=FormServiceExtensionParams(form_demands={"initial_form": initial_form})
        )


class FormServiceExtensionServer(BaseExtensionServer[FormServiceExtensionSpec, FormServiceExtensionMetadata]): ...


class FormServiceExtensionClient(BaseExtensionClient[FormServiceExtensionSpec, FormRender]): ...
