# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Awaitable
from uuid import UUID, uuid4

from pydantic import BaseModel, AwareDatetime, Field

from beeai_server.utils.utils import utc_now


class AsyncFile(BaseModel):
    filename: str
    content_type: str
    read: Callable[[int], Awaitable[bytes]]
    size: int | None = None


class File(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    file_size_bytes: int | None = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    created_by: UUID
