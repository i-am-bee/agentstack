# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PaginatedResult(BaseModel, Generic[T]):
    items: list[T]
    total_count: int
    has_more: bool = False
    next_page_token: str | None = None
