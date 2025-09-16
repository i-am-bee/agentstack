# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class UpdateVariablesRequest(BaseModel):
    variables: dict[str, str | None]


class ListVariablesSchema(BaseModel):
    variables: dict[str, str]
