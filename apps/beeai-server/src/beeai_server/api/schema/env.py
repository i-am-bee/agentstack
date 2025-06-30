# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class UpdateVariablesRequest(BaseModel):
    env: dict[str, str | None]


class ListVariablesSchema(BaseModel):
    env: dict[str, str]
