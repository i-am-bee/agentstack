# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class UpdateConfigurationRequest(BaseModel):
    default_llm_model: str | None = None
    default_embedding_model: str | None = None
