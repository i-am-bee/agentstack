# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, EmailStr, Field

from agentstack_server.domain.models.user import UserRole


class UserListQuery(BaseModel):
    limit: int = Field(default=40, ge=1, le=100)
    page_token: UUID | None = None
    email: str | None = Field(default=None, description="Filter by email (case-insensitive partial match)")


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    created_at: AwareDatetime
    role_updated_at: AwareDatetime | None


class ChangeRoleRequest(BaseModel):
    new_role: UserRole


class ChangeRoleResponse(BaseModel):
    user_id: UUID
    new_role: UserRole
