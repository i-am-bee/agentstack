# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from importlib.metadata import version

from agentstack_sdk.util.pydantic import apply_beeai_framework_pydantic_fix

__version__ = version("agentstack-sdk")

apply_beeai_framework_pydantic_fix()
