# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol, runtime_checkable

NOT_SET = object()


@runtime_checkable
class ITokenPasscodeRepository(Protocol):
    async def get(self, passcode: str, default: str | None = NOT_SET) -> str: ...
    async def set(self, passcode: str, token: dict) -> None: ...
    async def delete(self, passcode: str) -> None: ...
