# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import TypeVar

V = TypeVar("V")


def filter_dict(map: dict[str, V], value_to_exclude: V = None) -> dict[str, V]:
    """Remove entries with unwanted values (None by default) from dictionary."""
    return {filter: value for filter, value in map.items() if value is not value_to_exclude}
