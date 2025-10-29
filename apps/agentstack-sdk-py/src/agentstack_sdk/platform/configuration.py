# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pydantic

from agentstack_sdk.platform.client import PlatformClient, get_platform_client


class SystemConfiguration(pydantic.BaseModel):
    id: str
    default_llm_model: str | None = None
    default_embedding_model: str | None = None
    updated_at: pydantic.AwareDatetime
    created_by: str

    @staticmethod
    async def get(*, client: PlatformClient | None = None) -> SystemConfiguration:
        """Get the current system configuration."""
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(SystemConfiguration).validate_python(
                (await client.get(url="/api/v1/configurations/system")).raise_for_status().json()
            )

    @staticmethod
    async def update(
        *,
        default_llm_model: str | None = None,
        default_embedding_model: str | None = None,
        client: PlatformClient | None = None,
    ) -> SystemConfiguration:
        """Update the system configuration."""
        async with client or get_platform_client() as client:
            return pydantic.TypeAdapter(SystemConfiguration).validate_python(
                (
                    await client.put(
                        url="/api/v1/configurations/system",
                        json={
                            "default_llm_model": default_llm_model,
                            "default_embedding_model": default_embedding_model,
                        },
                    )
                )
                .raise_for_status()
                .json()
            )
