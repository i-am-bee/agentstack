# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from acp_sdk import AgentsListResponse as AcpAgentsListResponse

from beeai_server.domain.models.agent import Agent


class AgentsListResponse(AcpAgentsListResponse):
    agents: list[Agent]


class AgentReadResponse(Agent):
    pass
