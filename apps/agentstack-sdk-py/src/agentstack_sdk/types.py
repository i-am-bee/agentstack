# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Required, TypeAlias, TypedDict

from a2a.types import SecurityRequirement, SecurityScheme
from starlette.authentication import AuthenticationBackend

__all__ = [
    "JsonDict",
    "JsonPatch",
    "JsonPatchOp",
    "JsonValue",
    "SdkAuthenticationBackend",
]

if TYPE_CHECKING:
    JsonValue: TypeAlias = list["JsonValue"] | dict[str, "JsonValue"] | str | bool | int | float | None
    JsonDict: TypeAlias = dict[str, JsonValue]
else:
    from typing import Union  # noqa: F401

    from typing_extensions import TypeAliasType

    JsonValue = TypeAliasType("JsonValue", "Union[dict[str, JsonValue], list[JsonValue], str, int, float, bool, None]")
    JsonDict = TypeAliasType("JsonDict", "dict[str, JsonValue]")

class JsonPatchOp(TypedDict, total=False):
    """A single JSON Patch operation (RFC 6902), extended with 'str_ins' from json-crdt-patch."""

    op: Required[str]
    path: Required[str]
    value: JsonValue
    pos: int  # str_ins extension: insertion position


JsonPatch: TypeAlias = list[JsonPatchOp]


class A2ASecurity(TypedDict):
    security_requirements: list[SecurityRequirement]
    security_schemes: dict[str, SecurityScheme]


class SdkAuthenticationBackend(AuthenticationBackend, abc.ABC):
    @abc.abstractmethod
    def get_card_security_schemes(self) -> A2ASecurity: ...
