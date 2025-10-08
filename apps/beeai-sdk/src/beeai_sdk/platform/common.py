# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from enum import Enum, StrEnum
from typing import Generic, Literal, TypeAlias, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class _Undefined(Enum):
    undefined = "undefined"


undefined = _Undefined.undefined
Undefined: TypeAlias = Literal[_Undefined.undefined]


class PaginatedResult(BaseModel, Generic[T]):
    items: list[T]
    total_count: int
    has_more: bool = False
    next_page_token: str | None = None


class GithubVersionType(StrEnum):
    HEAD = "head"
    TAG = "tag"


class ResolvedGithubUrl(BaseModel):
    host: str = "github.com"
    org: str
    repo: str
    version: str
    version_type: GithubVersionType
    commit_hash: str
    path: str | None = None
