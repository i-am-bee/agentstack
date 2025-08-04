# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import httpx
import pydantic

from beeai_sdk.platform import get_client


class Variables(pydantic.BaseModel):
    env: dict[str, str] = pydantic.Field(default_factory=dict)

    async def save(
        self,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        _ = (
            await (client or get_client()).put(
                url="/api/v1/variables",
                json={"env": self.env},
            )
        ).raise_for_status()

    @staticmethod
    async def get(*, client: httpx.AsyncClient | None = None) -> Variables:
        return pydantic.TypeAdapter(Variables).validate_json(
            (await (client or get_client()).get(url="/api/v1/variables")).raise_for_status().content
        )
