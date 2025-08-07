# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import AwareDatetime, BaseModel, Field

from beeai_server.domain.models.common import Metadata
from beeai_server.domain.models.permissions import Permissions


class ContextCreateRequest(BaseModel):
    """Request schema for context creation."""

    metadata: Metadata | None = None


class ContextTokenCreateRequest(BaseModel):
    grant_global_permissions: Permissions = Field(
        default=Permissions(),
        description="Global permissions granted by the token. Must be subset of the users permissions",
    )
    grant_context_permissions: Permissions = Field(
        default=Permissions(),
        description="Context permissions granted by the token. Must be subset of the users permissions",
    )


class ContextTokenResponse(BaseModel):
    """Response schema for context token generation."""

    token: str
    expires_at: AwareDatetime | None
