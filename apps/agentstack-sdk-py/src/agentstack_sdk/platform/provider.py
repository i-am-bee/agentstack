# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import builtins
import typing
import urllib.parse
from contextlib import asynccontextmanager
from uuid import UUID

import pydantic
from a2a.client import ClientConfig, ClientFactory
from a2a.types import AgentCard

from agentstack_sdk.platform.client import PlatformClient, get_platform_client
from agentstack_sdk.util.utils import filter_dict


class ProviderErrorMessage(pydantic.BaseModel):
    message: str


class Provider(pydantic.BaseModel):
    id: str
    source: str
    origin: str
    source_type: typing.Literal["kagenti", "api"] = "api"
    created_at: pydantic.AwareDatetime
    updated_at: pydantic.AwareDatetime
    last_active_at: pydantic.AwareDatetime
    agent_card: AgentCard
    state: typing.Literal["online", "offline"] = "online"
    last_error: ProviderErrorMessage | None = None
    created_by: UUID

    @staticmethod
    async def create(
        *,
        location: str,
        agent_card: AgentCard | None = None,
        origin: str | None = None,
        client: PlatformClient | None = None,
    ) -> "Provider":
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Provider).validate_python(
                (
                    await client.post(
                        url="/api/v1/providers",
                        json=filter_dict(
                            {
                                "location": location,
                                "agent_card": agent_card.model_dump(mode="json") if agent_card else None,
                                "origin": origin,
                            }
                        ),
                    )
                )
                .raise_for_status()
                .json()
            )

    async def patch(
        self: "Provider" | str,
        *,
        location: str | None = None,
        agent_card: AgentCard | None = None,
        origin: str | None = None,
        client: PlatformClient | None = None,
    ) -> "Provider":
        # `self` has a weird type so that you can call both `instance.patch()` to update an instance, or `Provider.patch("123", ...)` to update a provider

        provider_id = self if isinstance(self, str) else self.id
        payload = filter_dict(
            {
                "location": location,
                "agent_card": agent_card.model_dump(mode="json") if agent_card else None,
                "origin": origin,
            }
        )
        if not payload:
            return await Provider.get(self)

        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Provider).validate_python(
                (await client.patch(url=f"/api/v1/providers/{provider_id}", json=payload)).raise_for_status().json()
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

    async def get(self: "Provider" | str, *, client: PlatformClient | None = None) -> "Provider":
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

    @staticmethod
    async def get_by_location(*, location: str, client: PlatformClient | None = None) -> "Provider":
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(Provider).validate_json(
                (await client.get(url=f"/api/v1/providers/by-location/{urllib.parse.quote(location, safe='')}"))
                .raise_for_status()
                .content
            )

    async def delete(self: "Provider" | str, *, client: PlatformClient | None = None) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `Provider.delete("123")`
        provider_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            _ = (await client.delete(f"/api/v1/providers/{provider_id}")).raise_for_status()

    @staticmethod
    async def list(
        *, origin: str | None = None, user_owned: bool | None = None, client: PlatformClient | None = None
    ) -> builtins.list["Provider"]:
        async with client or get_platform_client() as client:
            params = filter_dict({"origin": origin, "user_owned": user_owned})
            return pydantic.TypeAdapter(builtins.list[Provider]).validate_python(
                (
                    await client.get(
                        url="/api/v1/providers",
                        params=params,
                    )
                )
                .raise_for_status()
                .json()["items"]
            )
