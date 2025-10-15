# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
from datetime import timedelta
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
)

from beeai_server.domain.constants import DEFAULT_AUTO_STOP_TIMEOUT
from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.github import ResolvedGithubUrl
from beeai_server.utils.utils import utc_now

logger = logging.getLogger(__name__)


class BuildState(StrEnum):
    MISSING = "missing"
    IN_PROGRESS = "in_progress"
    BUILD_COMPLETED = "build_completed"
    COMPLETED = "completed"
    FAILED = "failed"


class AddProvider(BaseModel):
    """
    Will add a new provider or update an existing one with the same base docker image ID
    (docker registry + repository, excluding tag)
    """

    type: Literal["add_provider"] = "add_provider"
    auto_stop_timeout_sec: int | None = Field(
        default=None,
        gt=0,
        le=600,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )
    variables: dict[str, str] | None = None

    @property
    def auto_stop_timeout(self) -> timedelta:
        return timedelta(seconds=self.auto_stop_timeout_sec or int(DEFAULT_AUTO_STOP_TIMEOUT.total_seconds()))


class UpdateProvider(BaseModel):
    """Will update provider specified by ID"""

    type: Literal["update_provider"] = "update_provider"
    provider_id: UUID


class NoAction(BaseModel):
    type: Literal["no_action"] = "no_action"


type OnCompleteAction = AddProvider | UpdateProvider | NoAction


class ProviderBuild(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=utc_now)
    status: BuildState
    source: ResolvedGithubUrl
    destination: DockerImageID
    created_by: UUID
    on_complete: OnCompleteAction = NoAction()
    error_message: str | None = None
