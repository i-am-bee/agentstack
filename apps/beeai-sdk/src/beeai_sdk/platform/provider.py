# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing
from contextlib import asynccontextmanager
from datetime import timedelta

import pydantic
from a2a.client import ClientConfig, ClientFactory
from a2a.types import AgentCard

from beeai_sdk.platform.client import PlatformClient, get_platform_client


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
        agent_card: AgentCard | None = None,
        auto_remove: bool = False,
        client: PlatformClient | None = None,
    ) -> "Provider":
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Provider).validate_python(
                (
                    await client.post(
                        url="/api/v1/providers",
                        json={
                            "location": location,
                            "agent_card": agent_card.model_dump(mode="json") if agent_card else None,
                        },
                        params={"auto_remove": auto_remove},
                    )
                )
                .raise_for_status()
                .json()
            )

    @asynccontextmanager
    async def a2a_client(self, client: PlatformClient | None = None):
        async with client or get_platform_client() as client:
            yield ClientFactory(ClientConfig(httpx_client=client)).create(card=self.agent_card)

    @staticmethod
    async def preview(
        *,
        location: str,
        agent_card: AgentCard | None = None,
        client: PlatformClient | None = None,
    ) -> "Provider":
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Provider).validate_python(
                (
                    await client.post(
                        url="/api/v1/providers/preview",
                        json={
                            "location": location,
                            "agent_card": agent_card.model_dump(mode="json") if agent_card else None,
                        },
                    )
                )
                .raise_for_status()
                .json()
            )

    async def get(self: "Provider | str", /, *, client: PlatformClient | None = None) -> "Provider":
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `Provider.get("123")` to obtain a new instance
        provider_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            result = pydantic.TypeAdapter(Provider).validate_json(
                (await client.get(url=f"/api/v1/providers/{provider_id}")).raise_for_status().content
            )
        if isinstance(self, Provider):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def delete(self: "Provider | str", /, *, client: PlatformClient | None = None) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `Provider.delete("123")`
        provider_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            _ = (await client.delete(f"/api/v1/providers/{provider_id}")).raise_for_status()

    @staticmethod
    async def list(*, client: PlatformClient | None = None) -> list["Provider"]:
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(list[Provider]).validate_python(
                (await client.get(url="/api/v1/providers")).raise_for_status().json()["items"]
            )
