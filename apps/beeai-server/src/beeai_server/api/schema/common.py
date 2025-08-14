# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import Self
from uuid import UUID

from pydantic import BaseModel


class PaginatedResponse[BaseModelT: BaseModel](BaseModel):
    items: list[BaseModelT]
    total_count: int


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
