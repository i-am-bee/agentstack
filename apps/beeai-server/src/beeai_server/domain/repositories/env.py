# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import runtime_checkable, Protocol

NOT_SET = object()


@runtime_checkable
class IEnvVariableRepository(Protocol):
    async def get(self, key: str, default: str | None = NOT_SET) -> str: ...
    async def get_all(self) -> dict[str, str]: ...
    async def update(self, update: dict[str, str | None]) -> None: ...
