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
from typing import AsyncIterable
from uuid import UUID

from sqlalchemy import Table, Column, String, JSON, ForeignKey, UUID as SqlUUID, Text, Select, Row, DateTime
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import select, insert, delete

from beeai_server.domain.models.agent import Agent, AgentRunRequest
from beeai_server.domain.repositories.agent import IAgentRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

agents_table = Table(
    "agents",
    metadata,
    Column("id", SqlUUID, primary_key=True),
    Column("name", String(256), unique=True, nullable=False),
    Column("description", Text, nullable=True),
    Column("provider_id", ForeignKey("providers.id", ondelete="CASCADE"), nullable=False),
    Column("metadata", JSON, nullable=False),
)

agent_requests_table = Table(
    "agent_requests",
    metadata,
    Column("id", SqlUUID, primary_key=True),
    Column("acp_run_id", SqlUUID, nullable=True),
    Column("agent_id", SqlUUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=True),
)


class SqlAlchemyAgentRepository(IAgentRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def bulk_create(self, agents: list[Agent]) -> None:
        if not agents:
            return
        query = insert(agents_table).values(
            [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "provider_id": agent.metadata.provider_id,
                    "metadata": agent.metadata.model_dump(mode="json"),
                }
                for agent in agents
            ]
        )
        await self.connection.execute(query)

    async def list(self) -> AsyncIterable[Agent]:
        async for row in await self.connection.stream(select(agents_table)):
            yield self._to_agent(row)

    async def get_agent(self, *, agent_id: UUID) -> Agent:
        return await self._get_one(agents_table.select().where(agents_table.c.id == agent_id), id=agent_id)

    async def get_agent_by_name(self, *, name: str) -> Agent:
        return await self._get_one(agents_table.select().where(agents_table.c.name == name), id=name)

    def _to_agent(self, row: Row) -> Agent:
        return Agent.model_validate(
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "metadata": row.metadata,
            }
        )

    async def _get_one(self, query: Select, id: str):
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="agent", id=id)

        return self._to_agent(row)

    async def create_request(self, *, request: AgentRunRequest) -> None:
        query = agent_requests_table.insert().values(
            id=request.id,
            acp_run_id=request.acp_run_id,
            agent_id=request.agent_id,
            created_at=request.created_at,
        )
        await self.connection.execute(query)

    async def update_request(self, *, request: AgentRunRequest) -> None:
        query = (
            agent_requests_table.update()
            .where(agent_requests_table.c.id == request.id)
            .values(
                acp_run_id=request.acp_run_id,
                finished_at=request.finished_at,
            )
        )
        await self.connection.execute(query)

    async def delete_run(self, *, run_id: UUID) -> None:
        query = delete(agent_requests_table).where(agent_requests_table.c.id == run_id)
        await self.connection.execute(query)

    async def find_by_acp_run_id(self, *, run_id: UUID) -> Agent:
        result = await self.connection.execute(
            select(agents_table)
            .join(agent_requests_table, agents_table.c.id == agent_requests_table.c.agent_id)
            .where(agent_requests_table.c.acp_run_id == run_id)
            .limit(1)
        )
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="agent_run", id=run_id)

        return self._to_agent(row)

    async def delete_requests_older_than(
        self, *, finished_threshold: timedelta, stale_threshold: timedelta | None = None
    ) -> int:
        cond = agent_requests_table.c.finished_at < (utc_now() - finished_threshold)
        if stale_threshold:
            cond |= agent_requests_table.c.finished_at.is_(None) & (
                agent_requests_table.c.created_at < (utc_now() - stale_threshold)
            )
        query = agent_requests_table.delete().where(cond)
        result = await self.connection.execute(query)
        return result.rowcount
