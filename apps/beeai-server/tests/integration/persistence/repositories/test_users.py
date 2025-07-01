# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
import pytest_asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text

from beeai_server.domain.models.user import User, UserRole
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.user import SqlAlchemyUserRepository

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def test_user() -> User:
    """Create a test user for use in tests."""
    return User(
        email=f"test-{uuid.uuid4()}@example.com",
        role=UserRole.user,
    )


@pytest_asyncio.fixture
async def test_admin() -> User:
    """Create a test admin user for use in tests."""
    return User(
        email=f"admin-{uuid.uuid4()}@example.com",
        role=UserRole.admin,
    )


@pytest.mark.asyncio
async def test_create_user(db_transaction: AsyncConnection, test_user: User):
    # Create repository
    repository = SqlAlchemyUserRepository(connection=db_transaction)

    # Create user
    await repository.create(user=test_user)

    # Verify user was created
    result = await db_transaction.execute(text("SELECT * FROM users WHERE id = :id"), {"id": test_user.id})
    row = result.fetchone()
    assert row is not None
    assert str(row.id) == str(test_user.id)
    assert row.email == test_user.email
    assert row.role == test_user.role
    assert row.created_at == test_user.created_at


@pytest.mark.asyncio
async def test_get_user(db_transaction: AsyncConnection, test_user: User):
    # Create repository
    repository = SqlAlchemyUserRepository(connection=db_transaction)

    # Create user
    await repository.create(user=test_user)

    # Get user
    user = await repository.get(user_id=test_user.id)

    # Verify user
    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.role == test_user.role
    assert user.created_at == test_user.created_at


@pytest.mark.asyncio
async def test_get_user_not_found(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyUserRepository(connection=db_transaction)

    # Try to get non-existent user
    with pytest.raises(EntityNotFoundError):
        await repository.get(user_id=uuid.uuid4())

    # Try to get non-existent user by email
    with pytest.raises(EntityNotFoundError):
        await repository.get_by_email(email="nonexistent@example.com")


@pytest.mark.asyncio
async def test_get_user_by_email(db_transaction: AsyncConnection, test_user: User):
    # Create repository
    repository = SqlAlchemyUserRepository(connection=db_transaction)

    # Create user
    await repository.create(user=test_user)

    # Get user by email
    user = await repository.get_by_email(email=test_user.email)

    # Verify user
    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.role == test_user.role
    assert user.created_at == test_user.created_at


@pytest.mark.asyncio
async def test_delete_user(db_transaction: AsyncConnection, test_user: User):
    # Create repository
    repository = SqlAlchemyUserRepository(connection=db_transaction)

    # Create user
    await repository.create(user=test_user)

    # Verify user was created
    result = await db_transaction.execute(text("SELECT * FROM users WHERE id = :id"), {"id": test_user.id})
    assert result.fetchone() is not None

    # Delete user
    await repository.delete(user_id=test_user.id)

    # Verify user was deleted
    result = await db_transaction.execute(text("SELECT * FROM users WHERE id = :id"), {"id": test_user.id})
    assert result.fetchone() is None


@pytest.mark.asyncio
async def test_list_users(db_transaction: AsyncConnection, test_user: User, test_admin: User):
    # Create repository
    repository = SqlAlchemyUserRepository(connection=db_transaction)

    # Create users
    await repository.create(user=test_user)
    await repository.create(user=test_admin)

    # List users
    users = {user.id: user async for user in repository.list()}

    # Verify users
    assert len(users) >= 2  # There might be other users in the database
    assert test_user.id in users
    assert test_admin.id in users
    assert users[test_user.id].email == test_user.email
    assert users[test_user.id].role == test_user.role
    assert users[test_admin.id].email == test_admin.email
    assert users[test_admin.id].role == test_admin.role
