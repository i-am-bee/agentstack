# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from beeai_server.domain.models.common import Metadata
from beeai_server.domain.models.permissions import ResourceIdPermission


class ContextCreateRequest(BaseModel):
    """Request schema for context creation."""

    metadata: Metadata | None = None


class ContextPermissionsGrant(BaseModel):
    files: list[Literal["read", "write", "extract", "*"]] = []
    vector_stores: list[Literal["read", "write", "extract", "*"]] = []


class GlobalPermissionGrant(BaseModel):
    files: list[Literal["read", "write", "extract", "*"]] = []
    feedback: list[Literal["write"]] = []
    vector_stores: list[Literal["read", "write", "extract", "*"]] = []
    llm: list[Literal["*"] | ResourceIdPermission] = []
    embeddings: list[Literal["*"] | ResourceIdPermission] = []
    a2a_proxy: list[Literal["*"]] = []
    providers: list[Literal["read", "write", "*"]] = []  # write includes "show logs" permission
    variables: list[Literal["read", "write", "*"]] = []
    contexts: list[Literal["read", "write", "*"]] = []


class ContextTokenCreateRequest(BaseModel):
    grant_global_permissions: GlobalPermissionGrant = Field(
        default=GlobalPermissionGrant(),
        description="Global permissions granted by the token. Must be subset of the users permissions",
    )
    grant_context_permissions: ContextPermissionsGrant = Field(
        default=ContextPermissionsGrant(),
        description="Context permissions granted by the token. Must be subset of the users permissions",
    )


class ContextTokenResponse(BaseModel):
    """Response schema for context token generation."""

    token: str
    expires_at: AwareDatetime | None
