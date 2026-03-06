# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from importlib.metadata import version

from agentstack_sdk.util.pydantic import apply_compatibility_monkey_patching

__version__ = version("agentstack-sdk")

apply_compatibility_monkey_patching()
if os.getenv("AGENTSTACK_DONT_INJECT_A2A_VALIDATION", "").lower() not in {"true", "1"}:
    from agentstack_sdk.a2a.types import _inject_validation

    _inject_validation()
