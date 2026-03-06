# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from agentstack_sdk.a2a.types import RunYield


class InvalidYieldError(RuntimeError):
    def __init__(self, yielded_value: RunYield):
        super().__init__(f"Invalid yield of type: {type(yielded_value)}")
