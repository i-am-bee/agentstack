# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import timedelta
from typing import Protocol, runtime_checkable, AsyncIterator
from uuid import UUID
from beeai_server.domain.models.agent import Agent, AgentRunRequest


@runtime_checkable
class IAgentRepository(Protocol):
    async def bulk_create(self, agents: list[Agent]) -> None: ...
    async def get_agent(self, *, agent_id: UUID) -> Agent: ...
    async def list(self) -> AsyncIterator[Agent]:
        yield ...

    async def get_agent_by_name(self, *, name: str) -> Agent: ...
    async def create_request(self, *, request: AgentRunRequest) -> None: ...
    async def update_request(self, *, request: AgentRunRequest) -> None: ...
    async def delete_run(self, *, run_id: UUID) -> None: ...
    async def find_by_run_id(self, *, run_id: UUID) -> Agent: ...
    async def delete_requests_older_than(
        self, *, finished_threshold: timedelta, stale_threshold: timedelta | None = None
    ) -> int: ...
