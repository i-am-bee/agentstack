# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from uuid import UUID

from kink import inject
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import Boolean, Column, DateTime, Row, String, Table, bindparam, text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.domain.models.a2a_request import A2ARequestTask
from beeai_server.domain.repositories.a2a_request import IA2ARequestRepository
from beeai_server.exceptions import EntityNotFoundError, ForbiddenUpdateError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata
from beeai_server.utils.utils import utc_now

a2a_request_tasks_table = Table(
    "a2a_request_tasks",
    metadata,
    Column("task_id", String(256), primary_key=True),
    Column("created_by", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("provider_id", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_accessed_at", DateTime(timezone=True), nullable=False),
)

a2a_request_contexts_table = Table(
    "a2a_request_contexts",
    metadata,
    Column("context_id", String(256), primary_key=True),
    Column("created_by", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("provider_id", SQL_UUID, nullable=False),  # not using reference integrity for performance
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_accessed_at", DateTime(timezone=True), nullable=False),
)


@inject
class SqlAlchemyA2ARequestRepository(IA2ARequestRepository):
    def __init__(self, connection: AsyncConnection):
        self._connection = connection

    def _to_task(self, row: Row) -> A2ARequestTask:
        return A2ARequestTask.model_validate(
            {
                "task_id": row.task_id,
                "created_by": row.created_by,
                "provider_id": row.provider_id,
                "created_at": row.created_at,
                "last_accessed_at": row.last_accessed_at,
            }
        )

    async def track_request_ids_ownership(
        self,
        user_id: UUID,
        provider_id: UUID,
        task_id: str | None = None,
        context_id: str | None = None,
        allow_task_creation: bool = False,
    ) -> None:
        """
        Verify ownership and record/update identifiers in a SINGLE query.

        Args:
            allow_task_creation: If False, task_id must already exist in DB (client->server requests).
                                If True, task_id can be created (server responses).
        """

        # This handles all cases:
        # - New task_id/context_id: Creates ownership record (if allowed)
        # - Existing owned: Updates last_accessed_at and returns true
        # - Existing owned by OTHER user: ON CONFLICT WHERE clause prevents update, returns false

        now = utc_now()

        query = text("""
                     WITH task_insert AS (
                              INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at)
                                  SELECT :task_id, :user_id, :provider_id, :now, :now
                                  WHERE :task_id IS NOT NULL AND :allow_task_creation = true
                                  ON CONFLICT (task_id) DO NOTHING
                                  RETURNING true as inserted),
                          task_update AS (
                              UPDATE a2a_request_tasks
                                  SET last_accessed_at = :now
                                  WHERE task_id = :task_id AND created_by = :user_id
                                  RETURNING true as updated),
                          context_insert AS (
                              INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at)
                                  SELECT :context_id, :user_id, :provider_id, :now, :now
                                  WHERE :context_id IS NOT NULL
                                  ON CONFLICT (context_id) DO NOTHING
                                  RETURNING true as inserted),
                          context_update AS (
                              UPDATE a2a_request_contexts
                                  SET last_accessed_at = :now
                                  WHERE context_id = :context_id AND created_by = :user_id
                                  RETURNING true as updated)
                     SELECT CASE
                                WHEN :task_id IS NULL THEN true
                                WHEN EXISTS (SELECT 1 FROM task_insert) THEN true
                                WHEN EXISTS (SELECT 1 FROM task_update) THEN true
                                ELSE false
                                END as task_authorized,
                            CASE
                                WHEN :context_id IS NULL THEN true
                                WHEN EXISTS (SELECT 1 FROM context_insert) THEN true
                                WHEN EXISTS (SELECT 1 FROM context_update) THEN true
                                ELSE false
                                END as context_authorized
                     """).bindparams(
            bindparam("task_id", type_=String),
            bindparam("context_id", type_=String),
            bindparam("user_id", type_=SQL_UUID()),
            bindparam("provider_id", type_=SQL_UUID()),
            bindparam("allow_task_creation", type_=Boolean),
            bindparam("now", type_=DateTime(timezone=True)),
        )

        result = await self._connection.execute(
            query,
            {
                "task_id": task_id,
                "context_id": context_id,
                "user_id": user_id,
                "provider_id": provider_id,
                "allow_task_creation": allow_task_creation,
                "now": now,
            },
            execution_options={"compiled_cache": None},
        )

        if not (row := result.first()):
            raise RuntimeError("Unexpected query result")
        if not row.task_authorized:
            assert task_id
            raise EntityNotFoundError(entity="a2a_request_task", id=task_id)
        if not row.context_authorized:
            assert context_id
            raise ForbiddenUpdateError(entity="a2a_request_context", id=context_id)

    async def get_task(self, *, task_id: str, user_id: UUID) -> A2ARequestTask:
        """Get a task by task_id if owned by the user."""
        query = a2a_request_tasks_table.select().where(
            a2a_request_tasks_table.c.task_id == task_id, a2a_request_tasks_table.c.created_by == user_id
        )
        result = await self._connection.execute(query)
        if not (row := result.fetchone()):
            raise EntityNotFoundError(entity="a2a_request_task", id=task_id)
        return self._to_task(row)

    async def delete_tasks(self, *, older_than: timedelta) -> int:
        query = a2a_request_tasks_table.delete().where(
            a2a_request_tasks_table.c.last_accessed_at < utc_now() - older_than
        )
        result = await self._connection.execute(query)
        return result.rowcount

    async def delete_contexts(self, *, older_than: timedelta) -> int:
        query = a2a_request_contexts_table.delete().where(
            a2a_request_contexts_table.c.last_accessed_at < utc_now() - older_than
        )
        result = await self._connection.execute(query)
        return result.rowcount
