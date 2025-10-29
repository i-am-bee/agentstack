# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from agentstack_server.domain.models.file import File
from agentstack_server.exceptions import EntityNotFoundError
from agentstack_server.infrastructure.persistence.repositories.file import SqlAlchemyFileRepository
from agentstack_server.utils.utils import utc_now

pytestmark = pytest.mark.integration


async def create_user(db_transaction: AsyncConnection, user_id: uuid.UUID):
    await db_transaction.execute(
        text("INSERT INTO users (id, email, created_at, role) VALUES (:id, :email, :created_at, :role)"),
        {
            "id": user_id,
            "email": f"test-{user_id}@example.com",
            "role": "user",
            "created_at": utc_now(),
        },
    )


@pytest.fixture
async def test_user_id(db_transaction) -> uuid.UUID:
    """Create a test user for use in tests."""
    user_id = uuid.uuid4()
    await create_user(db_transaction, user_id)
    return user_id


@pytest.fixture
async def test_file(test_user_id: uuid.UUID) -> File:
    """Create a test file for use in tests."""
    return File(
        filename="test_file.txt",
        file_size_bytes=1024,
        content_type="text/plain",
        created_by=test_user_id,
    )


def db_file_for(user_id: uuid.UUID, filename: str = "test_file.txt", file_size_bytes: int = 1024) -> dict[str, Any]:
    return {
        "id": uuid.uuid4(),
        "filename": filename,
        "content_type": "text/plain",
        "file_size_bytes": file_size_bytes,
        "file_type": "user_upload",
        "created_at": utc_now(),
        "created_by": user_id,
    }


@pytest.fixture
async def db_test_file(db_transaction: AsyncConnection, test_user_id: uuid.UUID) -> dict[str, Any]:
    # Create file data
    file_data = db_file_for(test_user_id)
    # Insert file directly into database
    await db_transaction.execute(
        text(
            "INSERT INTO files (id, filename, content_type, file_size_bytes, file_type, created_at, created_by) "
            "VALUES (:id, :filename, :content_type, :file_size_bytes, :file_type, :created_at, :created_by)"
        ),
        file_data,
    )
    return file_data


async def test_create_file(db_transaction: AsyncConnection, test_file: File):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Create file
    await repository.create(file=test_file)

    # Verify file was created
    result = await db_transaction.execute(text("SELECT * FROM files WHERE id = :id"), {"id": test_file.id})
    row = result.fetchone()
    assert row is not None
    assert str(row.id) == str(test_file.id)
    assert row.filename == test_file.filename
    assert row.file_size_bytes == test_file.file_size_bytes
    assert row.created_at == test_file.created_at
    assert str(row.created_by) == str(test_file.created_by)


async def test_get_file(db_transaction: AsyncConnection, db_test_file: dict[str, Any]):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Get file
    file = await repository.get(file_id=db_test_file["id"])

    # Verify file
    assert file.id == db_test_file["id"]
    assert file.filename == db_test_file["filename"]
    assert file.content_type == db_test_file["content_type"]
    assert file.file_size_bytes == db_test_file["file_size_bytes"]
    assert str(file.created_by) == str(db_test_file["created_by"])


async def test_get_file_by_user(db_transaction: AsyncConnection, db_test_file: dict[str, Any], test_user_id: uuid.UUID):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Get file with user filter
    file = await repository.get(file_id=db_test_file["id"], user_id=test_user_id)

    # Verify file
    assert file.id == db_test_file["id"]
    assert file.filename == db_test_file["filename"]
    assert file.content_type == db_test_file["content_type"]
    assert file.file_size_bytes == db_test_file["file_size_bytes"]
    assert str(file.created_by) == str(db_test_file["created_by"])

    # Try to get file with wrong user
    other_user_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundError):
        await repository.get(file_id=db_test_file["id"], user_id=other_user_id)


async def test_get_file_not_found(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Try to get non-existent file
    with pytest.raises(EntityNotFoundError):
        await repository.get(file_id=uuid.uuid4())


async def test_delete_file(db_transaction: AsyncConnection, test_file: File):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Create file
    await repository.create(file=test_file)

    # Verify file was created
    result = await db_transaction.execute(text("SELECT * FROM files WHERE id = :id"), {"id": test_file.id})
    assert result.fetchone() is not None

    # Delete file
    await repository.delete(file_id=test_file.id)

    # Verify file was deleted
    result = await db_transaction.execute(text("SELECT * FROM files WHERE id = :id"), {"id": test_file.id})
    assert result.fetchone() is None


async def test_delete_file_by_user(db_transaction: AsyncConnection, test_file: File):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Create file
    await repository.create(file=test_file)

    # Verify file was created
    result = await db_transaction.execute(text("SELECT * FROM files WHERE id = :id"), {"id": test_file.id})
    assert result.fetchone() is not None

    # Try to delete file with wrong user
    other_user_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundError):
        await repository.delete(file_id=test_file.id, user_id=other_user_id)

    # Verify file still exists (wrong user couldn't delete it)
    result = await db_transaction.execute(text("SELECT * FROM files WHERE id = :id"), {"id": test_file.id})
    assert result.fetchone() is not None

    # Delete file with correct user
    await repository.delete(file_id=test_file.id, user_id=test_file.created_by)

    # Verify file was deleted
    result = await db_transaction.execute(text("SELECT * FROM files WHERE id = :id"), {"id": test_file.id})
    assert result.fetchone() is None


async def test_list_files(db_transaction: AsyncConnection, test_user_id: uuid.UUID):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Create another user
    other_user_id = uuid.uuid4()
    await create_user(db_transaction, other_user_id)

    # Create file data for test user
    user_files = [
        db_file_for(test_user_id, filename="test_file_1.txt", file_size_bytes=1024),
        db_file_for(test_user_id, filename="test_file_1.txt", file_size_bytes=2048),
    ]

    # Create file data for other user
    other_user_files = [db_file_for(other_user_id, filename="other_file.txt", file_size_bytes=4096)]

    # Insert files directly into database
    for file_data in user_files + other_user_files:
        await db_transaction.execute(
            text(
                "INSERT INTO files (id, filename, content_type, file_size_bytes, file_type, created_at, created_by) "
                "VALUES (:id, :filename, :content_type, :file_size_bytes, :file_type, :created_at, :created_by)"
            ),
            file_data,
        )

    # List all files
    all_files = {file.id: file async for file in repository.list()}
    assert len(all_files) == 3

    # List files for test user
    user_files_list = {file.id: file async for file in repository.list(user_id=test_user_id)}
    assert len(user_files_list) == 2
    for file_data in user_files:
        assert file_data["id"] in user_files_list
        assert user_files_list[file_data["id"]].filename == file_data["filename"]
        assert user_files_list[file_data["id"]].content_type == file_data["content_type"]
        assert user_files_list[file_data["id"]].file_size_bytes == file_data["file_size_bytes"]
        assert str(user_files_list[file_data["id"]].created_by) == str(file_data["created_by"])

    # List files for other user
    other_user_files_list = {file.id: file async for file in repository.list(user_id=other_user_id)}
    assert len(other_user_files_list) == 1
    for file_data in other_user_files:
        assert file_data["id"] in other_user_files_list
        assert other_user_files_list[file_data["id"]].filename == file_data["filename"]
        assert other_user_files_list[file_data["id"]].file_size_bytes == file_data["file_size_bytes"]
        assert str(other_user_files_list[file_data["id"]].created_by) == str(file_data["created_by"])


async def test_total_usage(db_transaction: AsyncConnection, test_user_id: uuid.UUID):
    # Create repository
    repository = SqlAlchemyFileRepository(connection=db_transaction)

    # Create another user
    other_user_id = uuid.uuid4()
    await create_user(db_transaction, other_user_id)

    # Create file data for test user
    user_files = [
        db_file_for(test_user_id, filename="test_file_1.txt", file_size_bytes=1024),
        db_file_for(test_user_id, filename="test_file_1.txt", file_size_bytes=2048),
    ]

    # Create file data for other user
    other_user_files = [db_file_for(other_user_id, filename="other_file.txt", file_size_bytes=4096)]

    # Insert files directly into database
    for file_data in user_files + other_user_files:
        await db_transaction.execute(
            text(
                "INSERT INTO files (id, filename, content_type, file_size_bytes, file_type, created_at, created_by) "
                "VALUES (:id, :filename, :content_type, :file_size_bytes, :file_type, :created_at, :created_by)"
            ),
            file_data,
        )

    # Get total usage for all users
    total_usage = await repository.total_usage()
    assert total_usage == 1024 + 2048 + 4096

    # Get total usage for test user
    user_total_usage = await repository.total_usage(user_id=test_user_id)
    assert user_total_usage == 1024 + 2048

    # Get total usage for other user
    other_user_total_usage = await repository.total_usage(user_id=other_user_id)
    assert other_user_total_usage == 4096
