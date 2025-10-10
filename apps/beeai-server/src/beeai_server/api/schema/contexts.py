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
    files: list[Literal["read", "write", "extract", "*"]] = Field(default_factory=list)
    vector_stores: list[Literal["read", "write", "extract", "*"]] = Field(default_factory=list)
    context_data: list[Literal["read", "write", "*"]] = Field(default_factory=list)


class GlobalPermissionGrant(BaseModel):
    files: list[Literal["read", "write", "extract", "*"]] = Field(default_factory=list)
    feedback: list[Literal["write"]] = Field(default_factory=list)
    vector_stores: list[Literal["read", "write", "extract", "*"]] = Field(default_factory=list)

    # openai proxy
    llm: list[Literal["*"] | ResourceIdPermission] = Field(default_factory=list)
    embeddings: list[Literal["*"] | ResourceIdPermission] = Field(default_factory=list)
    model_providers: list[Literal["read", "write", "*"]] = Field(default_factory=list)

    a2a_proxy: list[Literal["*"]] = Field(default_factory=list)

    # agent providers
    providers: list[Literal["read", "write", "*"]] = Field(
        default_factory=list
    )  # write includes "show logs" permission
    provider_variables: list[Literal["read", "write", "*"]] = Field(default_factory=list)

    contexts: list[Literal["read", "write", "*"]] = Field(default_factory=list)
    context_data: list[Literal["read", "write", "*"]] = Field(default_factory=list)

    mcp_providers: list[Literal["read", "write", "*"]] = Field(default_factory=list)
    mcp_tools: list[Literal["read", "*"]] = Field(default_factory=list)
    mcp_proxy: list[Literal["*"]] = Field(default_factory=list)


class ContextTokenCreateRequest(BaseModel):
    grant_global_permissions: GlobalPermissionGrant = Field(
        default_factory=GlobalPermissionGrant,
        description="Global permissions granted by the token. Must be subset of the users permissions",
    )
    grant_context_permissions: ContextPermissionsGrant = Field(
        default_factory=ContextPermissionsGrant,
        description="Context permissions granted by the token. Must be subset of the users permissions",
    )


class ContextTokenResponse(BaseModel):
    """Response schema for context token generation."""

    token: str
    expires_at: AwareDatetime | None


class ContextHistoryItemCreateRequest(RootModel[ContextHistoryItemData]):
    root: ContextHistoryItemData
