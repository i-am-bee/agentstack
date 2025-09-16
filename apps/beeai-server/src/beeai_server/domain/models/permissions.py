# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from beeai_server.domain.models.user import User


class ResourceIdPermission(BaseModel):
    id: str
    model_config = ConfigDict(frozen=True)


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
    vector_stores: SerializeAsAny[set[Literal["read", "write", "extract", "*"]]] = set()

    # openai proxy
    model_providers: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    llm: SerializeAsAny[set[Literal["*"] | ResourceIdPermission]] = set()
    embeddings: SerializeAsAny[set[Literal["*"] | ResourceIdPermission]] = set()

    a2a_proxy: SerializeAsAny[set[Literal["*"]]] = set()

    # agent providers
    providers: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()  # write includes "show logs" permission
    provider_variables: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()

    contexts: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    context_data: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()  # covers history (TODO: variables)
    mcp_providers: SerializeAsAny[set[Literal["read", "write", "*"]]] = set()
    mcp_tools: SerializeAsAny[set[Literal["read", "*"]]] = set()
    mcp_proxy: SerializeAsAny[set[Literal["*"]]] = set()

    allow_all: bool = Field(False, description="Admin override", init=False, exclude=True)

    @model_validator(mode="after")
    def freeze(self):
        self.model_config["frozen"] = False
        for key, value in self.model_dump(serialize_as_any=True).items():
            if isinstance(value, set):
                setattr(self, key, frozenset(value))
        self.model_config["frozen"] = True
        return self

    @classmethod
    def all(cls):
        return cls(allow_all=True)  # pyright: ignore [reportCallIssue] param intentionally hidden from the signature

    def check(self, required: Self) -> bool:
        """Check if required permissions are subset of current permissions."""
        if self.allow_all:
            return True

        my_permissions = self.model_dump(serialize_as_any=True)
        for key, required_permissions in required.model_dump(serialize_as_any=True).items():
            if "*" in my_permissions[key] or required_permissions.issubset(my_permissions[key]):
                continue
            return False

        return True

    def __or__(self, other: Self) -> Self:
        return self.union(other)

    def union(self, other: Self) -> Self:
        if self.allow_all or other.allow_all:
            return type(self).all()

        result = {}
        my_permissions = self.model_dump(serialize_as_any=True)
        for key, other_set in other.model_dump(serialize_as_any=True).items():
            result[key] = my_permissions[key].union(other_set)
            if "*" in result[key]:
                result[key] = {"*"}
        return type(self).model_validate(result)


class AuthorizedUser(BaseModel):
    user: User
    global_permissions: Permissions
    context_permissions: Permissions
    context_id: UUID | None = None
    token_context_id: UUID | None = None
