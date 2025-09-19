# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta
from enum import StrEnum
from typing import Any, Literal

import pydantic

from beeai_sdk.platform.client import PlatformClient, get_platform_client
from beeai_sdk.platform.common import PaginatedResult, ResolvedGithubUrl
from beeai_sdk.util.utils import filter_dict, parse_stream


class BuildState(StrEnum):
    MISSING = "missing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProviderBuild(pydantic.BaseModel):
    id: str
    created_at: pydantic.AwareDatetime
    status: BuildState
    source: ResolvedGithubUrl
    destination: str
    created_by: str

    @staticmethod
    async def create(*, location: str, client: PlatformClient | None = None) -> ProviderBuild:
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(ProviderBuild).validate_python(
                (await client.post(url="/api/v1/provider_builds", json={"location": location}))
                .raise_for_status()
                .json()
            )

    async def stream_logs(
        self: ProviderBuild | str, *, client: PlatformClient | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        # `self` has a weird type so that you can call both `instance.stream_logs()` or `ProviderBuild.stream_logs("123")`
        provider_build_id = self if isinstance(self, str) else self.id
        async with (
            client or get_platform_client() as client,
            client.stream(
                "GET",
                url=f"/api/v1/provider_builds/{provider_build_id}/logs",
                timeout=timedelta(hours=1).total_seconds(),
            ) as response,
        ):
            async for line in parse_stream(response):
                yield line

    async def get(self: ProviderBuild | str, *, client: PlatformClient | None = None) -> ProviderBuild:
        # `self` has a weird type so that you can call both `instance.get()` to update an instance, or `ProviderBuild.get("123")` to obtain a new instance
        provider_build_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            result = pydantic.TypeAdapter(ProviderBuild).validate_json(
                (await client.get(url=f"/api/v1/provider_builds/{provider_build_id}")).raise_for_status().content
            )
        if isinstance(self, ProviderBuild):
            self.__dict__.update(result.__dict__)
            return self
        return result

    async def delete(self: ProviderBuild | str, *, client: PlatformClient | None = None) -> None:
        # `self` has a weird type so that you can call both `instance.delete()` or `ProviderBuild.delete("123")`
        provider_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            _ = (await client.delete(f"/api/v1/provider_builds/{provider_id}")).raise_for_status()

    @staticmethod
    async def list(
        *,
        page_token: str | None = None,
        limit: int | None = None,
        order: Literal["asc"] | Literal["desc"] | None = "asc",
        order_by: Literal["created_at"] | Literal["updated_at"] | None = None,
        client: PlatformClient | None = None,
    ) -> PaginatedResult[ProviderBuild]:
        # `self` has a weird type so that you can call both `instance.list_history()` or `ProviderBuild.list_history("123")`
        async with client or get_platform_client() as platform_client:
            return pydantic.TypeAdapter(PaginatedResult[ProviderBuild]).validate_python(
                (
                    await platform_client.get(
                        url="/api/v1/provider_builds",
                        params=filter_dict(
                            {"page_token": page_token, "limit": limit, "order": order, "order_by": order_by}
                        ),
                    )
                )
                .raise_for_status()
                .json()
            )
