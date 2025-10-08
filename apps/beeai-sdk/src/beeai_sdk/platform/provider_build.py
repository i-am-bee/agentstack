# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta
from enum import StrEnum
from typing import Any, Literal, TypeAlias
from uuid import UUID

import pydantic

from beeai_sdk.platform.client import PlatformClient, get_platform_client
from beeai_sdk.platform.common import PaginatedResult, ResolvedGithubUrl, Undefined, undefined
from beeai_sdk.util.utils import filter_dict, parse_stream


class BuildState(StrEnum):
    MISSING = "missing"
    IN_PROGRESS = "in_progress"
    BUILD_COMPLETED = "build_completed"
    COMPLETED = "completed"
    FAILED = "failed"


class AddProvider(pydantic.BaseModel):
    """
    Will add a new provider or update an existing one with the same base docker image ID
    (docker registry + repository, excluding tag)
    """

    type: Literal["add_provider"] = "add_provider"
    auto_stop_timeout_sec: int | Undefined = pydantic.Field(
        default=undefined,
        gt=0,
        le=600,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )
    variables: dict[str, str] | None = None


class UpdateProvider(pydantic.BaseModel):
    """Will update provider specified by ID"""

    type: Literal["update_provider"] = "update_provider"
    provider_id: UUID


class NoAction(pydantic.BaseModel):
    type: Literal["no_action"] = "no_action"


OnCompleteAction: TypeAlias = AddProvider | UpdateProvider | NoAction


class ProviderBuild(pydantic.BaseModel):
    id: str
    created_at: pydantic.AwareDatetime
    status: BuildState
    source: ResolvedGithubUrl
    destination: str
    created_by: str
    error_message: str | None = None

    @staticmethod
    async def create(
        *, location: str, client: PlatformClient | None = None, on_complete: OnCompleteAction | None = None
    ) -> ProviderBuild:
        on_complete = on_complete or NoAction()
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(ProviderBuild).validate_python(
                (
                    await client.post(
                        url="/api/v1/provider_builds",
                        json={"location": location, "on_complete": filter_dict(on_complete.model_dump(), undefined)},
                    )
                )
                .raise_for_status()
                .json()
            )

    @staticmethod
    async def preview(
        *, location: str, client: PlatformClient | None = None, on_complete: OnCompleteAction | None = None
    ) -> ProviderBuild:
        on_complete = on_complete or NoAction()
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(ProviderBuild).validate_python(
                (
                    await client.post(
                        url="/api/v1/provider_builds/preview",
                        json={"location": location, "on_complete": filter_dict(on_complete.model_dump(), undefined)},
                    )
                )
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
        provider_build_id = self if isinstance(self, str) else self.id
        async with client or get_platform_client() as client:
            _ = (await client.delete(f"/api/v1/provider_builds/{provider_build_id}")).raise_for_status()

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
