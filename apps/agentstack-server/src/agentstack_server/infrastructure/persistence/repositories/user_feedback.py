# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import UUID

from kink import inject
from sqlalchemy import ARRAY, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Table, Text, select
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy.ext.asyncio import AsyncConnection

from agentstack_server.domain.models.user_feedback import UserFeedback
from agentstack_server.domain.repositories.user_feedback import IUserFeedbackRepository
from agentstack_server.infrastructure.persistence.repositories.db_metadata import metadata
from agentstack_server.infrastructure.persistence.repositories.provider import providers_table
from agentstack_server.infrastructure.persistence.repositories.utils import cursor_paginate

user_feedback_table = Table(
    "user_feedback",
    metadata,
    Column("id", SQL_UUID, primary_key=True),
    Column("provider_id", ForeignKey("providers.id", ondelete="CASCADE"), nullable=False),
    Column("task_id", SQL_UUID, nullable=False),
    Column("context_id", SQL_UUID, nullable=False),
    Column("trace_id", String(256), nullable=True),
    Column("rating", Integer, nullable=False),
    Column("message", Text, nullable=False),
    Column("comment", Text, nullable=True),
    Column("comment_tags", ARRAY(Text), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("created_by", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    CheckConstraint("rating IN (1, -1)", name="rating_check"),
)


@inject
class SqlAlchemyUserFeedbackRepository(IUserFeedbackRepository):
    def __init__(self, connection: AsyncConnection):
        self.connection = connection

    async def create(self, *, user_feedback: UserFeedback) -> None:
        query = user_feedback_table.insert().values(
            id=user_feedback.id,
            provider_id=user_feedback.provider_id,
            task_id=user_feedback.task_id,
            context_id=user_feedback.context_id,
            trace_id=user_feedback.trace_id,
            rating=user_feedback.rating,
            comment=user_feedback.comment,
            comment_tags=user_feedback.comment_tags,
            message=user_feedback.message,
            created_at=user_feedback.created_at,
            created_by=user_feedback.created_by,
        )
        await self.connection.execute(query)

    async def list(
        self,
        *,
        provider_created_by: UUID | None = None,
        provider_id: UUID | None = None,
        limit: int = 50,
        after_cursor: UUID | None = None,
    ) -> tuple[list[UserFeedback], int, bool]:
        query = select(
            user_feedback_table,
            providers_table.c.agent_card["name"].label("agent_name"),
        ).join(providers_table, user_feedback_table.c.provider_id == providers_table.c.id)

        if provider_created_by is not None:
            query = query.where(providers_table.c.created_by == provider_created_by)

        if provider_id is not None:
            query = query.where(user_feedback_table.c.provider_id == provider_id)

        result = await cursor_paginate(
            connection=self.connection,
            query=query,
            order_column=user_feedback_table.c.created_at,
            id_column=user_feedback_table.c.id,
            limit=limit,
            after_cursor=after_cursor,
            order="desc",
        )

        feedback_list = [UserFeedback.model_validate(dict(row._mapping)) for row in result.items]

        return feedback_list, result.total_count, result.has_more
