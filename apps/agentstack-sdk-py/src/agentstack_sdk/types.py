# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    JsonValue: TypeAlias = list["JsonValue"] | dict[str, "JsonValue"] | str | bool | int | float | None
    JsonDict: TypeAlias = dict[str, JsonValue]
else:
    from typing import Union

    from typing_extensions import TypeAliasType

    JsonValue = TypeAliasType("JsonValue", "Union[dict[str, JsonValue], list[JsonValue], str, int, float, bool, None]")  # noqa: UP007
    JsonDict = TypeAliasType("JsonDict", "dict[str, JsonValue]")
