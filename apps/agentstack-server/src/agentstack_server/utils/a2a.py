# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any


def get_extension(agent_card: dict[str, Any], uri: str) -> dict[str, Any] | None:
    try:
        capabilities = agent_card.get("capabilities", {})
        extensions = capabilities.get("extensions", [])
        return next(ext for ext in extensions if ext.get("uri") == uri)
    except StopIteration:
        return None
