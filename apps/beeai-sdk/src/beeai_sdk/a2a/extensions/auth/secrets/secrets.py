# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing
from typing import TYPE_CHECKING

import pydantic
from a2a.types import Message as A2AMessage

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from beeai_sdk.a2a.types import AgentMessage, AuthRequired

if TYPE_CHECKING:
    from beeai_sdk.server.context import RunContext


class SecretDemand(pydantic.BaseModel):
    name: str
    description: str | None = None


class SecretFulfillment(pydantic.BaseModel):
    secret: str


class SecretsServiceExtensionParams(pydantic.BaseModel):
    secret_demands: dict[str, SecretDemand]


class SecretsServiceExtensionMetadata(pydantic.BaseModel):
    secret_fulfillments: dict[str, SecretFulfillment] = {}


class SecretsExtensionSpec(BaseExtensionSpec[SecretsServiceExtensionParams | None]):
    URI: str = "https://a2a-extensions.beeai.dev/auth/secrets/v1"

    @classmethod
    def single_demand(cls, name: str, key: str | None = None, description: str | None = None) -> typing.Self:
        return cls(
            params=SecretsServiceExtensionParams(
                secret_demands={key or "default": SecretDemand(description=description, name=name)}
            )
        )


class SecretsExtensionServer(BaseExtensionServer[SecretsExtensionSpec, SecretsServiceExtensionMetadata]):
    def handle_incoming_message(self, message: A2AMessage, context: "RunContext"):
        super().handle_incoming_message(message, context)
        self.context = context

    def parse_secret_response(self, message: A2AMessage) -> SecretsServiceExtensionMetadata:
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Secrets has not been provided in response.")

        return SecretsServiceExtensionMetadata.model_validate(data)

    async def request_secrets(self, params: SecretsServiceExtensionParams) -> SecretsServiceExtensionMetadata:
        resume = await self.context.yield_async(
            AuthRequired(
                message=AgentMessage(
                    metadata={self.spec.URI: params.model_dump(mode="json")},
                )
            )
        )
        if isinstance(resume, A2AMessage):
            return self.parse_secret_response(message=resume)
        else:
            raise ValueError("Secrets has not been provided in response.")


class SecretsExtensionClient(BaseExtensionClient[SecretsExtensionSpec, SecretsServiceExtensionParams]): ...
