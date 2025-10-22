# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from beeai_server.api.schema.common import PaginationQuery
from beeai_server.domain.models.provider_build import BuildConfiguration, BuildState, NoAction, OnCompleteAction
from beeai_server.utils.github import GithubUrl


class CreateProviderBuildRequest(BaseModel):
    location: GithubUrl
    on_complete: OnCompleteAction = Field(default_factory=NoAction)
    build_configuration: BuildConfiguration | None = None


class ProviderBuildListQuery(PaginationQuery):
    status: BuildState | None = None
    user_owned: bool | None = None
