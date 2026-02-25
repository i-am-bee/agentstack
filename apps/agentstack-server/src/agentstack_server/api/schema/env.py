# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateVariablesRequest(BaseModel):
    variables: dict[str, str | None] = Field(max_length=100)


class ListVariablesSchema(BaseModel):
    variables: dict[str, str]
