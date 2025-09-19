# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
)

from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.github import ResolvedGithubUrl
from beeai_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


class BuildState(StrEnum):
    MISSING = "missing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    # CANCELLED = "cancelled" # TODO


class ProviderBuild(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=utc_now)
    status: BuildState
    source: ResolvedGithubUrl
    destination: DockerImageID
    created_by: UUID
