# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from kink import inject
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Column, DateTime, Row, String, Table
from sqlalchemy.ext.asyncio import AsyncConnection

from agentstack_server.domain.models.common import PaginatedResult
from agentstack_server.domain.models.user import User
from agentstack_server.domain.repositories.user import IUserRepository
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.infrastructure.persistence.repositories.db_metadata import metadata
from agentstack_server.infrastructure.persistence.repositories.utils import cursor_paginate

users_table = Table(
    "users",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("email", String(256), nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
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
        )
        await self.connection.execute(query)

    def _to_user(self, row: Row):
        return User.model_validate(
            {
                "id": row.id,
                "email": row.email,
                "created_at": row.created_at,
            }
        )

    async def get(self, *, user_id: UUID) -> User:
        query = users_table.select().where(users_table.c.id == user_id)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="user", id=user_id)
        return self._to_user(row)

    async def get_by_email(self, *, email: str) -> User:
        query = users_table.select().where(users_table.c.email == email)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="user", id=email)
        return self._to_user(row)

    async def delete(self, *, user_id: UUID) -> int:
        query = users_table.delete().where(users_table.c.id == user_id)
        result = await self.connection.execute(query)
        if not result.rowcount:
            raise EntityNotFoundError(entity="user", id=user_id)
        return result.rowcount

    async def list(
        self,
        *,
        limit: int,
        page_token: UUID | None = None,
        email: str | None = None,
    ) -> PaginatedResult[User]:
        query = users_table.select()

        if email is not None:
            query = query.where(users_table.c.email.ilike(f"%{email}%"))

        result = await cursor_paginate(
            connection=self.connection,
            query=query,
            order_column=users_table.c.created_at,
            id_column=users_table.c.id,
            limit=limit,
            after_cursor=page_token,
            order="desc",
        )

        users = [self._to_user(row) for row in result.items]
        return PaginatedResult(items=users, total_count=result.total_count, has_more=result.has_more)
