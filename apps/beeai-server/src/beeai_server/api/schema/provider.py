# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from datetime import timedelta

from a2a.types import AgentCard
from pydantic import BaseModel, Field

from beeai_server.domain.constants import DEFAULT_AUTO_STOP_TIMEOUT, Undefined, undefined
from beeai_server.domain.models.provider import ProviderLocation


class CreateProviderRequest(BaseModel):
    location: ProviderLocation
    agent_card: AgentCard | None = None
    variables: dict[str, str] | None = None
    origin: str | None = Field(
        default=None,
        description=(
            "A unique origin of the provider: most often a docker or github repository url (without tag). "
            "This is used to determine multiple versions of the same agent."
            "If not set, will be generated from location."
        ),
    )
    auto_stop_timeout_sec: int = Field(
        default=int(DEFAULT_AUTO_STOP_TIMEOUT.total_seconds()),
        gt=0,
        le=600,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )

    @property
    def auto_stop_timeout(self) -> timedelta:
        return timedelta(seconds=self.auto_stop_timeout_sec)


class PatchProviderRequest(BaseModel):
    location: ProviderLocation | None = None
    agent_card: AgentCard | None = None
    variables: dict[str, str] | None = None
    origin: str | None | Undefined = Field(
        default=undefined,
        description=(
            "A unique origin of the provider: most often a docker or github repository url (without tag). "
            "This is used to determine multiple versions of the same agent. "
            "If left undefined, this will not be changed and can be inconsistent with location. "
            "If None, origin will be recomputed from location."
        ),
    )
    auto_stop_timeout_sec: int | Undefined = Field(
        default=undefined,
        gt=0,
        le=600,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )

    @property
    def auto_stop_timeout(self) -> timedelta | Undefined:
        if self.auto_stop_timeout_sec is undefined:
            return undefined
        return timedelta(seconds=self.auto_stop_timeout_sec)
