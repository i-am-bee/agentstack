# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

import pydantic
from a2a.types import AgentCard

from agentstack_sdk.platform.client import PlatformClient, get_platform_client


class DiscoveryState(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProviderDiscovery(pydantic.BaseModel):
    id: UUID
    created_at: pydantic.AwareDatetime
    status: DiscoveryState
    docker_image: str
    created_by: UUID
    agent_card: AgentCard | None = None
    error_message: str | None = None

    @staticmethod
    async def create(
        *,
        docker_image: str,
        client: PlatformClient | None = None,
    ) -> "ProviderDiscovery":
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(ProviderDiscovery).validate_python(
                (
                    await client.post(
                        url="/api/v1/providers/discovery",
                        json={"docker_image": docker_image},
                    )
                )
                .raise_for_status()
                .json()
            )

    async def get(self: "ProviderDiscovery" | str, *, client: PlatformClient | None = None) -> "ProviderDiscovery":
        discovery_id = self if isinstance(self, str) else str(self.id)
        async with client or get_platform_client() as client:
            result = pydantic.TypeAdapter(ProviderDiscovery).validate_json(
                (await client.get(url=f"/api/v1/providers/discovery/{discovery_id}")).raise_for_status().content
            )
        if isinstance(self, ProviderDiscovery):
            self.__dict__.update(result.__dict__)
            return self
        return result
