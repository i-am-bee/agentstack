# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import pydantic
from a2a.server.agent_execution.context import RequestContext
from a2a.types import Message as A2AMessage
from opentelemetry import trace
from typing_extensions import override

from agentstack_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec
from agentstack_sdk.a2a.types import AgentMessage, AuthRequired
from agentstack_sdk.util.pydantic import REDACT_SECRETS, REVEAL_SECRETS, SecureBaseModel
from agentstack_sdk.util.telemetry import flatten_dict

__all__ = [
    "A2A_EXTENSION_SECRETS_REQUESTED",
    "A2A_EXTENSION_SECRETS_RESOLVED",
    "SecretDemand",
    "SecretFulfillment",
    "SecretsExtensionClient",
    "SecretsExtensionServer",
    "SecretsExtensionSpec",
    "SecretsServiceExtensionMetadata",
    "SecretsServiceExtensionParams",
]

if TYPE_CHECKING:
    from agentstack_sdk.server.context import RunContext

A2A_EXTENSION_SECRETS_REQUESTED = "a2a_extension.secrets.requested"
A2A_EXTENSION_SECRETS_RESOLVED = "a2a_extension.secrets.resolved"


class SecretDemand(pydantic.BaseModel):
    name: str
    description: str | None = None


class SecretFulfillment(SecureBaseModel):
    secret: pydantic.SecretStr


class SecretsServiceExtensionParams(pydantic.BaseModel):
    secret_demands: dict[str, SecretDemand]


class SecretsServiceExtensionMetadata(pydantic.BaseModel):
    secret_fulfillments: dict[str, SecretFulfillment] = {}


class SecretsExtensionSpec(BaseExtensionSpec[SecretsServiceExtensionParams | None]):
    URI: str = "https://a2a-extensions.agentstack.beeai.dev/auth/secrets/v1"

    @classmethod
    def single_demand(cls, name: str, key: str | None = None, description: str | None = None) -> Self:
        return cls(
            params=SecretsServiceExtensionParams(
                secret_demands={key or "default": SecretDemand(description=description, name=name)}
            )
        )


class SecretsExtensionServer(BaseExtensionServer[SecretsExtensionSpec, SecretsServiceExtensionMetadata]):
    context: RunContext

    @override
    def handle_incoming_message(self, message: A2AMessage, run_context: RunContext, request_context: RequestContext):
        super().handle_incoming_message(message, run_context, request_context)
        self.context = run_context

    def parse_secret_response(self, message: A2AMessage) -> SecretsServiceExtensionMetadata:
        if not message or not message.metadata or not (data := message.metadata.get(self.spec.URI)):
            raise ValueError("Secrets has not been provided in response.")

        return SecretsServiceExtensionMetadata.model_validate(data)

    async def request_secrets(self, params: SecretsServiceExtensionParams) -> SecretsServiceExtensionMetadata:
        span = trace.get_current_span()
        span.add_event(
            A2A_EXTENSION_SECRETS_REQUESTED,
            attributes=flatten_dict(params.model_dump(context={REDACT_SECRETS: True})),
        )
        resume = await self.context.yield_async(
            AuthRequired(
                message=AgentMessage(
                    metadata={self.spec.URI: params.model_dump(mode="json", context={REVEAL_SECRETS: True})},
                )
            )
        )
        if isinstance(resume, A2AMessage):
            response = self.parse_secret_response(message=resume)
            span.add_event(
                A2A_EXTENSION_SECRETS_RESOLVED,
                attributes=flatten_dict(response.model_dump(context={REDACT_SECRETS: True})),
            )
            return response
        else:
            raise ValueError("Secrets has not been provided in response.")


class SecretsExtensionClient(BaseExtensionClient[SecretsExtensionSpec, SecretsServiceExtensionParams]): ...
