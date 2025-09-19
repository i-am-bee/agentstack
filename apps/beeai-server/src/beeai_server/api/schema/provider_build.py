# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel

from beeai_server.utils.github import GithubUrl


class CreateProviderBuildRequest(BaseModel):
    location: GithubUrl
