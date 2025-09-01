# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Optional


class JwksDict:
    def __init__(self, data: dict[str, dict] | None = None):
        self.data: dict[str, dict] = data or {}

    def __getitem__(self, key: str) -> dict:
        return self.data[key]

    def __setitem__(self, key: str, value: dict) -> None:
        self.data[key] = value

    def get(self, issuer: str) -> dict | None:
        return self.data.get(issuer)

    def issuers(self) -> list[str]:
        return list(self.data.keys())
