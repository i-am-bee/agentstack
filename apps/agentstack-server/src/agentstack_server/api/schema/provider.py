# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from datetime import timedelta

from a2a.types import AgentCard
from pydantic import BaseModel, Field

from agentstack_server.domain.constants import DEFAULT_AUTO_STOP_TIMEOUT
from agentstack_server.domain.models.provider import ProviderLocation


class CreateProviderRequest(BaseModel):
    location: ProviderLocation
    agent_card: AgentCard | None = None
    variables: dict[str, str] | None = None
    origin: str | None = Field(
        default=None,
        description=(
            "A unique origin of the provider: most often a docker or github repository url (without tag). "
            "This is used to determine multiple versions of the same agent."
        ),
    )
    auto_stop_timeout_sec: int | None = Field(
        default=None,
        gt=0,
        le=1800,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )

    @property
    def auto_stop_timeout(self) -> timedelta:
        return timedelta(seconds=self.auto_stop_timeout_sec or int(DEFAULT_AUTO_STOP_TIMEOUT.total_seconds()))


class PatchProviderRequest(BaseModel):
    location: ProviderLocation | None = None
    agent_card: AgentCard | None = None
    variables: dict[str, str] | None = None
    origin: str | None = Field(
        default=None,
        description=(
            "A unique origin of the provider: most often a docker or github repository url (without tag). "
            "This is used to determine multiple versions of the same agent. "
            "None means that origin will be recomputed from location. To preserve original value, set it explicitly."
        ),
    )
    auto_stop_timeout_sec: int | None = Field(
        default=None,
        gt=0,
        le=1800,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )

    @property
    def auto_stop_timeout(self) -> timedelta | None:
        return timedelta(seconds=self.auto_stop_timeout_sec) if self.auto_stop_timeout_sec else None
