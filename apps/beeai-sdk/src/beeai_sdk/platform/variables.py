# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from beeai_sdk.platform.client import PlatformClient, get_platform_client


class Variables(dict[str, str]):
    async def save(
        self: Variables | dict[str, str | None] | dict[str, str],
        *,
        client: PlatformClient | None = None,
    ) -> None:
        """
        Save variables to the BeeAI platform. Does not delete keys unless explicitly set to None.

        Can be used as a class method: Variables.save({"key": "value", ...})
        ...or as an instance method: variables.save()
        """
        async with client or get_platform_client() as client:
            _ = (
                await client.put(
                    url="/api/v1/variables",
                    json={"env": self},
                )
            ).raise_for_status()

    async def load(self: Variables | None = None, *, client: PlatformClient | None = None) -> Variables:
        """
        Load variables from the BeeAI platform.

        Can be used as a class method: variables = Variables.load()
        ...or as an instance method to update the instance: variables.load()
        """
        async with client or get_platform_client() as client:
            new_variables: dict[str, str] = (await client.get(url="/api/v1/variables")).raise_for_status().json()["env"]
        if isinstance(self, Variables):
            self.clear()
            self.update(new_variables)
            return self
        return Variables(new_variables)
