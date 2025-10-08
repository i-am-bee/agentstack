# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta

from a2a.types import AgentCard
from pydantic import BaseModel, Field

from beeai_server.domain.models.provider import ProviderLocation


class CreateProviderRequest(BaseModel):
    location: ProviderLocation
    agent_card: AgentCard | None = None
    variables: dict[str, str] | None = None
    auto_stop_timeout_sec: int = Field(
        default=int(timedelta(minutes=5).total_seconds()),
        gt=0,
        le=600,
        description=(
            "Timeout after which the agent provider will be automatically downscaled if unused."
            "Contact administrator if you need to increase this value."
        ),
    )
