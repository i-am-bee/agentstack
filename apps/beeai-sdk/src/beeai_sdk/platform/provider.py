# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from datetime import timedelta

import httpx
import pydantic
from a2a.types import AgentCard

from beeai_sdk.platform import get_client


class ProviderErrorMessage(pydantic.BaseModel):
    message: str


class EnvVar(pydantic.BaseModel):
    name: str
    description: str | None = None
    required: bool = False


class Provider(pydantic.BaseModel):
    id: str
    auto_stop_timeout: timedelta
    source: str
    registry: str | None = None
    auto_remove: bool = False
    created_at: pydantic.AwareDatetime
    last_active_at: pydantic.AwareDatetime
    agent_card: AgentCard
    state: typing.Literal["missing", "starting", "ready", "running", "error"] = "missing"
    last_error: ProviderErrorMessage | None = None
    missing_configuration: list[EnvVar] = pydantic.Field(default_factory=list)

    @staticmethod
    async def create(
        *,
        location: str,
        agent_card: AgentCard,
        auto_remove: bool = False,
        client: httpx.AsyncClient | None = None,
    ) -> Provider:
        return pydantic.TypeAdapter(Provider).validate_python(
            (
                await (client or get_client()).post(
                    url="/api/v1/providers",
                    json={"location": location, "agent_card": agent_card.model_dump(mode="json")},
                    params={"auto_remove": auto_remove},
                )
            )
            .raise_for_status()
            .json()
        )

    @staticmethod
    async def preview(
        *,
        location: str,
        agent_card: AgentCard,
        client: httpx.AsyncClient | None = None,
    ) -> Provider:
        return pydantic.TypeAdapter(Provider).validate_python(
            (
                await (client or get_client()).post(
                    url="/api/v1/providers/preview",
                    json={"location": location, "agent_card": agent_card.model_dump(mode="json")},
                )
            )
            .raise_for_status()
            .json()
        )

    async def get(self: Provider | str, /, *, client: httpx.AsyncClient | None = None) -> Provider:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `Provider.get("123")` to obtain a new instance
        provider_id = self if isinstance(self, str) else self.id
        result = pydantic.TypeAdapter(Provider).validate_json(
            (await (client or get_client()).get(url=f"/api/v1/providers/{provider_id}")).raise_for_status().content
        )
        if isinstance(self, Provider):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def delete(self: Provider | str, /, *, client: httpx.AsyncClient | None = None) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `Provider.delete("123")`
        provider_id = self if isinstance(self, str) else self.id
        _ = (await (client or get_client()).delete(f"/api/v1/providers/{provider_id}")).raise_for_status()

    @staticmethod
    async def list(*, client: httpx.AsyncClient | None = None) -> list[Provider]:
        return pydantic.TypeAdapter(list[Provider]).validate_python(
            (await (client or get_client()).get(url="/api/v1/providers")).raise_for_status().json()["items"]
        )
