# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from agentstack_server.domain.models.a2a_request import A2ARequestTask
from agentstack_server.exceptions import EntityNotFoundError, ForbiddenUpdateError
from agentstack_server.infrastructure.persistence.repositories.requests import SqlAlchemyA2ARequestRepository
from agentstack_server.utils.utils import utc_now

pytestmark = pytest.mark.integration


@pytest.fixture
def user1_id() -> UUID:
    """First test user ID."""
    return uuid.uuid4()


@pytest.fixture
def user2_id() -> UUID:
    """Second test user ID."""
    return uuid.uuid4()


@pytest.fixture
def provider_id() -> UUID:
    """Test provider ID."""
    return uuid.uuid4()


# ================================ track_request_ids_ownership tests ================================


async def test_track_new_task_with_creation_allowed(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test creating a new task when allow_task_creation=True."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Track a new task with creation allowed
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        task_id="new-task-1",
        allow_task_creation=True,
    )

    # Verify task was created in database
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "new-task-1"},
    )
    row = result.fetchone()
    assert row is not None
    assert row.task_id == "new-task-1"
    assert row.created_by == user1_id
    assert row.provider_id == provider_id
    assert row.created_at is not None
    assert row.last_accessed_at is not None


async def test_track_new_task_with_creation_not_allowed(
    db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID
):
    """Test that new task creation fails when allow_task_creation=False."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Attempt to track a new task with creation not allowed
    with pytest.raises(EntityNotFoundError) as exc_info:
        await repository.track_request_ids_ownership(
            user_id=user1_id,
            provider_id=provider_id,
            task_id="nonexistent-task",
            allow_task_creation=False,
        )

    assert exc_info.value.entity == "a2a_request_task"
    assert exc_info.value.id == "nonexistent-task"

    # Verify task was NOT created in database
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "nonexistent-task"},
    )
    assert result.fetchone() is None


async def test_track_existing_task_owned_by_same_user(
    db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID
):
    """Test accessing an existing task owned by the same user updates last_accessed_at."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a task with an old timestamp
    old_time = utc_now() - timedelta(hours=1)
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :old_time, :old_time)"
        ),
        {"task_id": "existing-task", "created_by": user1_id, "provider_id": provider_id, "old_time": old_time},
    )

    # Get initial timestamp
    result = await db_transaction.execute(
        text("SELECT last_accessed_at FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "existing-task"},
    )
    initial_timestamp = result.fetchone().last_accessed_at

    # Track the existing task (this should update last_accessed_at to NOW())
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        task_id="existing-task",
        allow_task_creation=False,
    )

    # Verify last_accessed_at was updated
    result = await db_transaction.execute(
        text("SELECT last_accessed_at FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "existing-task"},
    )
    new_timestamp = result.fetchone().last_accessed_at
    assert new_timestamp > initial_timestamp


async def test_track_existing_task_owned_by_different_user(
    db_transaction: AsyncConnection, user1_id: UUID, user2_id: UUID, provider_id: UUID
):
    """Test that accessing a task owned by a different user fails."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a task owned by user1
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :now, :now)"
        ),
        {"task_id": "user1-task", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Try to access as user2
    with pytest.raises(EntityNotFoundError) as exc_info:
        await repository.track_request_ids_ownership(
            user_id=user2_id,
            provider_id=provider_id,
            task_id="user1-task",
            allow_task_creation=False,
        )

    assert exc_info.value.entity == "a2a_request_task"
    assert exc_info.value.id == "user1-task"


async def test_track_new_context(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test creating a new context."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Track a new context
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        context_id="new-context-1",
    )

    # Verify context was created in database
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "new-context-1"},
    )
    row = result.fetchone()
    assert row is not None
    assert row.context_id == "new-context-1"
    assert row.created_by == user1_id
    assert row.provider_id == provider_id
    assert row.created_at is not None
    assert row.last_accessed_at is not None


async def test_track_existing_context_owned_by_same_user(
    db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID
):
    """Test accessing an existing context owned by the same user updates last_accessed_at."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a context with an old timestamp
    old_time = utc_now() - timedelta(hours=1)
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:context_id, :created_by, :provider_id, :old_time, :old_time)"
        ),
        {"context_id": "existing-context", "created_by": user1_id, "provider_id": provider_id, "old_time": old_time},
    )

    # Get initial timestamp
    result = await db_transaction.execute(
        text("SELECT last_accessed_at FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "existing-context"},
    )
    initial_timestamp = result.fetchone().last_accessed_at

    # Track the existing context (this should update last_accessed_at to NOW())
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        context_id="existing-context",
    )

    # Verify last_accessed_at was updated
    result = await db_transaction.execute(
        text("SELECT last_accessed_at FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "existing-context"},
    )
    new_timestamp = result.fetchone().last_accessed_at
    assert new_timestamp > initial_timestamp


async def test_track_existing_context_owned_by_different_user(
    db_transaction: AsyncConnection, user1_id: UUID, user2_id: UUID, provider_id: UUID
):
    """Test that accessing a context owned by a different user fails."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a context owned by user1
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:context_id, :created_by, :provider_id, :now, :now)"
        ),
        {"context_id": "user1-context", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Try to access as user2
    with pytest.raises(ForbiddenUpdateError) as exc_info:
        await repository.track_request_ids_ownership(
            user_id=user2_id,
            provider_id=provider_id,
            context_id="user1-context",
        )

    assert exc_info.value.entity == "a2a_request_context"
    assert exc_info.value.id == "user1-context"


async def test_track_both_task_and_context(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test tracking both task_id and context_id in a single call."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Track both new task and context
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        task_id="both-task-1",
        context_id="both-context-1",
        allow_task_creation=True,
    )

    # Verify both were created
    task_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "both-task-1"},
    )
    assert task_result.fetchone() is not None

    context_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "both-context-1"},
    )
    assert context_result.fetchone() is not None


async def test_track_both_task_and_context_task_owned_by_different_user(
    db_transaction: AsyncConnection, user1_id: UUID, user2_id: UUID, provider_id: UUID
):
    """Test that when task is owned by different user, the operation fails even if context would succeed."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a task owned by user1
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :now, :now)"
        ),
        {"task_id": "user1-task-2", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Try to track with user2 (task fails, context would succeed)
    with pytest.raises(EntityNotFoundError) as exc_info:
        await repository.track_request_ids_ownership(
            user_id=user2_id,
            provider_id=provider_id,
            task_id="user1-task-2",
            context_id="new-context-2",
            allow_task_creation=False,
        )

    assert exc_info.value.entity == "a2a_request_task"
    assert exc_info.value.id == "user1-task-2"


async def test_track_both_task_and_context_context_owned_by_different_user(
    db_transaction: AsyncConnection, user1_id: UUID, user2_id: UUID, provider_id: UUID
):
    """Test that when context is owned by different user, the operation fails even if task would succeed."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a context owned by user1
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:context_id, :created_by, :provider_id, :now, :now)"
        ),
        {"context_id": "user1-context-2", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Try to track with user2 (context fails, task would succeed)
    with pytest.raises(ForbiddenUpdateError) as exc_info:
        await repository.track_request_ids_ownership(
            user_id=user2_id,
            provider_id=provider_id,
            task_id="new-task-3",
            context_id="user1-context-2",
            allow_task_creation=True,
        )

    assert exc_info.value.entity == "a2a_request_context"
    assert exc_info.value.id == "user1-context-2"


async def test_track_null_task_id_succeeds(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test that passing None as task_id succeeds (returns task_authorized=true)."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Should not raise any exception
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        task_id=None,
        context_id="context-only",
    )

    # Verify only context was created
    context_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "context-only"},
    )
    assert context_result.fetchone() is not None


async def test_track_null_context_id_succeeds(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test that passing None as context_id succeeds (returns context_authorized=true)."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Should not raise any exception
    await repository.track_request_ids_ownership(
        user_id=user1_id,
        provider_id=provider_id,
        task_id="task-only",
        context_id=None,
        allow_task_creation=True,
    )

    # Verify only task was created
    task_result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "task-only"},
    )
    assert task_result.fetchone() is not None


# ================================ get_task tests ================================


async def test_get_task_success(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test getting a task that exists and is owned by the user."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a task
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :now, :now)"
        ),
        {"task_id": "get-task-1", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Get the task
    task = await repository.get_task(task_id="get-task-1", user_id=user1_id)

    # Verify task
    assert isinstance(task, A2ARequestTask)
    assert task.task_id == "get-task-1"
    assert task.created_by == user1_id
    assert task.provider_id == provider_id
    assert task.created_at is not None
    assert task.last_accessed_at is not None


async def test_get_task_not_found(db_transaction: AsyncConnection, user1_id: UUID):
    """Test getting a task that doesn't exist."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Try to get non-existent task
    with pytest.raises(EntityNotFoundError) as exc_info:
        await repository.get_task(task_id="nonexistent-task", user_id=user1_id)

    assert exc_info.value.entity == "a2a_request_task"
    assert exc_info.value.id == "nonexistent-task"


async def test_get_task_owned_by_different_user(
    db_transaction: AsyncConnection, user1_id: UUID, user2_id: UUID, provider_id: UUID
):
    """Test getting a task that exists but is owned by a different user."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a task owned by user1
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :now, :now)"
        ),
        {"task_id": "user1-get-task", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Try to get as user2
    with pytest.raises(EntityNotFoundError) as exc_info:
        await repository.get_task(task_id="user1-get-task", user_id=user2_id)

    assert exc_info.value.entity == "a2a_request_task"
    assert exc_info.value.id == "user1-get-task"


# ================================ delete_tasks tests ================================


async def test_delete_tasks_older_than_timedelta(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test deleting tasks older than a specified timedelta."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create an old task (5 days old)
    old_time = utc_now() - timedelta(days=5)
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :old_time, :old_time)"
        ),
        {"task_id": "old-task", "created_by": user1_id, "provider_id": provider_id, "old_time": old_time},
    )

    # Create a recent task (1 hour old)
    recent_time = utc_now() - timedelta(hours=1)
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :recent_time, :recent_time)"
        ),
        {"task_id": "recent-task", "created_by": user1_id, "provider_id": provider_id, "recent_time": recent_time},
    )

    # Delete tasks older than 3 days
    await repository.delete_tasks(older_than=timedelta(days=3))

    # Verify old task was deleted
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "old-task"},
    )
    assert result.fetchone() is None

    # Verify recent task still exists
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "recent-task"},
    )
    assert result.fetchone() is not None


async def test_delete_tasks_no_tasks_to_delete(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test deleting tasks when no tasks match the criteria."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a recent task
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_tasks (task_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:task_id, :created_by, :provider_id, :now, :now)"
        ),
        {"task_id": "recent-task-2", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Delete tasks older than 1 day (should delete nothing)
    await repository.delete_tasks(older_than=timedelta(days=1))

    # Verify task still exists
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_tasks WHERE task_id = :task_id"),
        {"task_id": "recent-task-2"},
    )
    assert result.fetchone() is not None


# ================================ delete_contexts tests ================================


async def test_delete_contexts_older_than_timedelta(db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID):
    """Test deleting contexts older than a specified timedelta."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create an old context (5 days old)
    old_time = utc_now() - timedelta(days=5)
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:context_id, :created_by, :provider_id, :old_time, :old_time)"
        ),
        {"context_id": "old-context", "created_by": user1_id, "provider_id": provider_id, "old_time": old_time},
    )

    # Create a recent context (1 hour old)
    recent_time = utc_now() - timedelta(hours=1)
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:context_id, :created_by, :provider_id, :recent_time, :recent_time)"
        ),
        {
            "context_id": "recent-context",
            "created_by": user1_id,
            "provider_id": provider_id,
            "recent_time": recent_time,
        },
    )

    # Delete contexts older than 3 days
    await repository.delete_contexts(older_than=timedelta(days=3))

    # Verify old context was deleted
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "old-context"},
    )
    assert result.fetchone() is None

    # Verify recent context still exists
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "recent-context"},
    )
    assert result.fetchone() is not None


async def test_delete_contexts_no_contexts_to_delete(
    db_transaction: AsyncConnection, user1_id: UUID, provider_id: UUID
):
    """Test deleting contexts when no contexts match the criteria."""
    repository = SqlAlchemyA2ARequestRepository(connection=db_transaction)

    # Create a recent context
    now = utc_now()
    await db_transaction.execute(
        text(
            "INSERT INTO a2a_request_contexts (context_id, created_by, provider_id, created_at, last_accessed_at) "
            "VALUES (:context_id, :created_by, :provider_id, :now, :now)"
        ),
        {"context_id": "recent-context-2", "created_by": user1_id, "provider_id": provider_id, "now": now},
    )

    # Delete contexts older than 1 day (should delete nothing)
    await repository.delete_contexts(older_than=timedelta(days=1))

    # Verify context still exists
    result = await db_transaction.execute(
        text("SELECT * FROM a2a_request_contexts WHERE context_id = :context_id"),
        {"context_id": "recent-context-2"},
    )
    assert result.fetchone() is not None
