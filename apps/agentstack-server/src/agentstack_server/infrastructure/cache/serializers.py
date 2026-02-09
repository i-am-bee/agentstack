# Copyright 2026 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json

from pydantic import BaseModel

from agentstack_server.service_layer.cache import ISerializer
from agentstack_server.types import JsonValue


class JsonSerializer[T: JsonValue](ISerializer[T]):
    def dumps(self, value: T) -> str:
        return json.dumps(value)

    def loads(self, value: str) -> T:
        return json.loads(value)


class PydanticSerializer[T: BaseModel](ISerializer[T]):
    def __init__(self, model: type[T]) -> None:
        super().__init__()
        self.model = model

    def dumps(self, value: T) -> str:
        return value.model_dump_json()

    def loads(self, value: str) -> T:
        return self.model.model_validate_json(value)
