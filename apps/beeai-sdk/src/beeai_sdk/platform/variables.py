# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import httpx

from beeai_sdk.platform.context import get_client


class Variables(dict[str, str]):
    async def save(
        self: Variables | dict[str, str],
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Save variables to the BeeAI platform. Does not delete keys unless explicitly set to None.

        Can be used as a class method: Variables.save({"key": "value", ...})
        ...or as an instance method: variables.save()
        """
        _ = (
            await (client or get_client()).put(
                url="/api/v1/variables",
                json={"env": self},
            )
        ).raise_for_status()

    async def load(self: Variables | None = None, *, client: httpx.AsyncClient | None = None) -> Variables:
        """
        Load variables from the BeeAI platform.

        Can be used as a class method: variables = Variables.load()
        ...or as an instance method to update the instance: variables.load()
        """
        new_variables: dict[str, str] = (
            (await (client or get_client()).get(url="/api/v1/variables")).raise_for_status().json()
        )
        if isinstance(self, Variables):
            self.clear()
            self.update(new_variables)
            return self
        return Variables(new_variables)
