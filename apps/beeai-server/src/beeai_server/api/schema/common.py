# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[BaseModelT]):
    items: list[BaseModelT]
    total_count: int


class ErrorStreamResponseError(BaseModel, extra="allow"):
    status_code: int
    type: str
    detail: str


class ErrorStreamResponse(BaseModel, extra="allow"):
    error: ErrorStreamResponseError


class EntityModel(BaseModel):
    def __class_getitem__(cls, model: type[BaseModel]):
        if not model.model_fields.get("id"):
            raise TypeError(f"Class {model.__name__} cannot is missing the id attribute")

        class ModelOutput(model):
            id: UUID

        ModelOutput.__name__ = f"{model.__name__}Response"

        return ModelOutput
