# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field


class PaginationQuery(BaseModel):
    limit: int = Field(default=40, ge=1, le=100)
    after: UUID | None = None
    order: str = Field(default="desc", pattern="^(asc|desc)$")
    order_by: str = Field(default="created_at", pattern="^created_at|updated_at$")


class ErrorStreamResponseError(BaseModel, extra="allow"):
    status_code: int
    type: str
    detail: str


class ErrorStreamResponse(BaseModel, extra="allow"):
    error: ErrorStreamResponseError


class EntityModel[T: BaseModel]:
    def __new__(cls, model: T) -> Self:
        assert getattr(model, "id", None)
        return model  # pyright: ignore [reportReturnType]

    def __class_getitem__(cls, model: type[T]) -> type[T]:  # pyright: ignore [reportIncompatibleMethodOverride]
        if not model.model_fields.get("id"):
            raise TypeError(f"Class {model.__name__} is missing the id attribute")

        class ModelOutput(model):
            id: UUID

        ModelOutput.__name__ = f"{model.__name__}Response"

        return ModelOutput  # pyright: ignore [reportReturnType]
