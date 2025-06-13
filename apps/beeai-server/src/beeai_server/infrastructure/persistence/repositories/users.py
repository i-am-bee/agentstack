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

from uuid import UUID

from kink import inject
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import Table, Column, String, DateTime, Row, select, delete, UUID as SqlUUID, Enum

from beeai_server.domain.models.user import User, UserRole
from beeai_server.domain.repositories.users import IUserRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

users_table = Table(
    "users",
    metadata,
    Column("id", SqlUUID, primary_key=True),
    Column("email", String(256), nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("role", Enum(UserRole), nullable=False),
)


@inject
class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, user: User) -> None:
        query = users_table.insert().values(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            role=user.role,
        )
        await self.connection.execute(query)

    def _to_user(self, row: Row):
        return User.model_validate(
            {
                "id": row.id,
                "email": row.email,
                "created_at": row.created_at,
                "role": row.role,
            }
        )

    async def get(self, *, user_id: UUID) -> User:
        query = select(users_table).where(users_table.c.id == user_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="user", id=user_id)
        return self._to_user(row)

    async def get_by_email(self, *, email: str) -> User:
        query = select(users_table).where(users_table.c.email == email)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="user", id=email)
        return self._to_user(row)

    async def delete(self, *, user_id: UUID) -> None:
        query = delete(users_table).where(users_table.c.id == user_id)
        await self.connection.execute(query)

    async def list(self):
        query = users_table.select()
        async for row in await self.connection.stream(query):
            yield self._to_user(row)
