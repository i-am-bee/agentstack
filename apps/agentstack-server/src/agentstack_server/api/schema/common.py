# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from uuid import UUID

from pydantic import BaseModel, Field


class PaginationQuery(BaseModel):
    limit: int = Field(default_factory=lambda: 40, ge=1, le=100)
    page_token: UUID | None = None
    order: str = Field(default_factory=lambda: "desc", pattern="^(asc|desc)$")
    order_by: str = Field(default_factory=lambda: "created_at", pattern="^created_at|updated_at$")


class ErrorStreamResponseError(BaseModel, extra="allow"):
    status_code: int
    type: str
    detail: str


class ErrorStreamResponse(BaseModel, extra="allow"):
    error: ErrorStreamResponseError


class EntityModel[T: BaseModel]:
    def __new__(cls, model: T) -> T:
        assert getattr(model, "id", None)
        return model

    def __class_getitem__(cls, model: type[T]) -> type[T]:  # pyrefly: ignore[no-matching-overload]
        if not model.model_fields.get("id"):  # pyrefly: ignore[no-matching-overload]
            raise TypeError(f"Class {model.__name__} is missing the id attribute")

        class ModelOutput(model):  # pyrefly: ignore[invalid-inheritance]
            id: UUID

        ModelOutput.__name__ = f"{model.__name__}Response"

        return ModelOutput  # pyrefly: ignore[bad-return]
