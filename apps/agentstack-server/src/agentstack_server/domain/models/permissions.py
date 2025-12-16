# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from agentstack_server.domain.models.user import User


class ResourceIdPermission(BaseModel):
    id: str
    model_config = ConfigDict(frozen=True)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, ResourceIdPermission):
            return self.id == other.id
        return False


class Permissions(BaseModel):
    model_config = ConfigDict(frozen=True, validate_default=True)

    # Hybrid types - make the class hashable but keep a nice interface:
    #   - constructor accepts a set (for idiomatic Annotations)
    #   - each set is replaced with a frozenset instance during validation
    #   - SerializeAsAny is required to allow duck typing:
    #       https://docs.pydantic.dev/latest/concepts/serialization/#serializing-with-duck-typing

    system_configuration: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()

    files: SerializeAsAny[set[Literal["read", "write", "extract", "*"]]] = set()
    feedback: SerializeAsAny[set[Literal["write"]]] = set()
    vector_stores: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    variables: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()

    # openai proxy
    model_providers: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    llm: SerializeAsAny[set[Literal["*"] | ResourceIdPermission]] = set()
    embeddings: SerializeAsAny[set[Literal["*"] | ResourceIdPermission]] = set()

    a2a_proxy: SerializeAsAny[set[Literal["*"]]] = set()

    # agent providers
    providers: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()  # write includes "show logs" permission
    provider_variables: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    provider_builds: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()  # write includes "show logs" permission

    contexts: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    context_data: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()  # covers history (TODO: variables)
    mcp_providers: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    mcp_tools: SerializeAsAny[set[Literal["read", "*"]]] = set()
    mcp_proxy: SerializeAsAny[set[Literal["*"]]] = set()

    # connectors
    connectors: SerializeAsAny[set[Literal["read", "write", "proxy", "*"]]] = set()

    allow_all: bool = Field(False, description="Admin override", init=False, exclude=True)

    @classmethod
    def _iter_permission_keys(cls):
        """Iterate over permission field keys, excluding special fields like allow_all."""
        for key in cls.model_fields:
            if key != "allow_all":
                yield key

    @model_validator(mode="after")
    def freeze(self):
        self.model_config["frozen"] = False
        for key in type(self).model_fields.keys():
            value = getattr(self, key)
            if isinstance(value, set):
                # Convert ResourceIdPermission objects to ensure they're hashable
                frozen_value = frozenset(value)
                setattr(self, key, frozen_value)
        self.model_config["frozen"] = True
        return self

    @classmethod
    def all(cls):
        return cls(allow_all=True)  # pyright: ignore [reportCallIssue] param intentionally hidden from the signature

    def check(self, required: Self) -> bool:
        """Check if required permissions are subset of current permissions."""
        if self.allow_all:
            return True

        for key in self._iter_permission_keys():
            my_perms = getattr(self, key)
            required_perms = getattr(required, key)
            if "*" in my_perms or required_perms.issubset(my_perms):
                continue
            return False

        return True

    def __or__(self, other: Self) -> Self:
        return self.union(other)

    def union(self, other: Self) -> Self:
        if self.allow_all or other.allow_all:
            return type(self).all()

        result = {}
        for key in self._iter_permission_keys():
            my_set = getattr(self, key)
            other_set = getattr(other, key)
            result[key] = my_set.union(other_set)
            if "*" in result[key]:
                result[key] = {"*"}
        return type(self).model_validate(result)


class AuthorizedUser(BaseModel):
    user: User
    global_permissions: Permissions
    context_permissions: Permissions
    context_id: UUID | None = None
    token_context_id: UUID | None = None
