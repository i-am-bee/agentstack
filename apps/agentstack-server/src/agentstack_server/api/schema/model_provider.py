# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, HttpUrl, Secret

from agentstack_server.domain.models.model_provider import ModelCapability, ModelProviderType


class CreateModelProviderRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    type: ModelProviderType
    base_url: HttpUrl
    watsonx_project_id: str | None = None
    watsonx_space_id: str | None = None
    api_key: Secret[str]


class MatchModelsRequest(BaseModel):
    suggested_models: list[str] | None = None
    capability: ModelCapability
    score_cutoff: float = 0.4
