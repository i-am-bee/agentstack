# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCard
from pydantic import BaseModel

from beeai_server.domain.models.provider import ProviderLocation


class CreateProviderRequest(BaseModel):
    location: ProviderLocation
    agent_card: AgentCard | None = None
    variables: dict[str, str] | None = None
