# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

type JsonValue = dict[str, JsonValue] | list[JsonValue] | str | int | float | bool | None
