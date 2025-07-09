# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, EmailStr, Field

from beeai_server.utils.utils import utc_now


class UserRole(StrEnum):
    admin = "admin"
    user = "user"


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: UserRole = UserRole.user
    email: EmailStr
    created_at: AwareDatetime = Field(default_factory=utc_now)
