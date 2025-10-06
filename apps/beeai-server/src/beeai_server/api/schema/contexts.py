# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, RootModel

from beeai_server.api.schema.common import PaginationQuery
from beeai_server.domain.models.common import Metadata, MetadataPatch
from beeai_server.domain.models.context import ContextHistoryItemData
from beeai_server.domain.models.permissions import ResourceIdPermission


class ContextCreateRequest(BaseModel):
    """Request schema for context creation."""

    metadata: Metadata | None = None


class ContextUpdateRequest(BaseModel):
    """Request schema for context update."""

    metadata: Metadata | None = None


class ContextPatchMetadataRequest(BaseModel):
    """Request schema for patching context metadata."""

    metadata: MetadataPatch


class ContextListQuery(PaginationQuery):
    include_empty: bool = True


class ContextPermissionsGrant(BaseModel):
    files: list[Literal["read", "write", "extract", "*"]] = []
    vector_stores: list[Literal["read", "write", "extract", "*"]] = []
    context_data: list[Literal["read", "write", "*"]] = []


class GlobalPermissionGrant(BaseModel):
    files: list[Literal["read", "write", "extract", "*"]] = []
    feedback: list[Literal["write"]] = []
    vector_stores: list[Literal["read", "write", "extract", "*"]] = []

    # openai proxy
    llm: list[Literal["*"] | ResourceIdPermission] = []
    embeddings: list[Literal["*"] | ResourceIdPermission] = []
    model_providers: list[Literal["read", "write", "*"]] = []

    a2a_proxy: list[Literal["*"]] = []

    # agent providers
    providers: list[Literal["read", "write", "*"]] = []  # write includes "show logs" permission
    provider_variables: list[Literal["read", "write", "*"]] = []

    contexts: list[Literal["read", "write", "*"]] = []
    context_data: list[Literal["read", "write", "*"]] = []

    mcp_providers: list[Literal["read", "write", "*"]] = []
    mcp_tools: list[Literal["read", "*"]] = []
    mcp_proxy: list[Literal["*"]] = []


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


class ContextHistoryItemCreateRequest(RootModel[ContextHistoryItemData]):
    root: ContextHistoryItemData
