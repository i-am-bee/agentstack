# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration, PersistenceConfiguration
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.env import SqlAlchemyEnvVariableRepository

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
def encryption_config() -> Configuration:
    """Create a test configuration with an encryption key."""
    # Generate a new Fernet key for testing
    config = Configuration(persistence=PersistenceConfiguration(encryption_key=Fernet.generate_key().decode()))
    return config


@pytest.mark.asyncio
async def test_update_and_get(db_transaction: AsyncConnection, encryption_config: Configuration):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "TEST_KEY_1": "test_value_1",
        "TEST_KEY_2": "test_value_2",
    }

    # Update variables
    await repository.update(variables)

    # Verify variables were created in the database (encrypted)
    result = await db_transaction.execute(text("SELECT * FROM variables"))
    rows = result.fetchall()
    assert len(rows) == 2

    # Get variables
    value1 = await repository.get(key="TEST_KEY_1")
    value2 = await repository.get(key="TEST_KEY_2")

    # Verify values
    assert value1 == variables["TEST_KEY_1"]
    assert value2 == variables["TEST_KEY_2"]


@pytest.mark.asyncio
async def test_get_with_default(db_transaction: AsyncConnection, encryption_config: Configuration):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Get non-existent variable with default
    value = await repository.get(key="NON_EXISTENT_KEY", default="default_value")

    # Verify default value is returned
    assert value == "default_value"


@pytest.mark.asyncio
async def test_get_not_found(db_transaction: AsyncConnection, encryption_config: Configuration):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Try to get non-existent variable without default
    with pytest.raises(EntityNotFoundError):
        await repository.get(key="NON_EXISTENT_KEY")


@pytest.mark.asyncio
async def test_update_remove(db_transaction: AsyncConnection, encryption_config: Configuration):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "TEST_KEY_1": "test_value_1",
        "TEST_KEY_2": "test_value_2",
    }

    # Update variables
    await repository.update(variables)

    # Verify variables were created
    result = await db_transaction.execute(text("SELECT * FROM variables"))
    assert len(result.fetchall()) == 2

    # Update with one variable set to None (should remove it)
    await repository.update({"TEST_KEY_1": None})

    # Verify TEST_KEY_1 was removed
    result = await db_transaction.execute(text("SELECT * FROM variables WHERE key = 'TEST_KEY_1'"))
    assert result.fetchone() is None

    # Verify TEST_KEY_2 still exists
    result = await db_transaction.execute(text("SELECT * FROM variables WHERE key = 'TEST_KEY_2'"))
    assert result.fetchone() is not None


@pytest.mark.asyncio
async def test_get_all(db_transaction: AsyncConnection, encryption_config: Configuration):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "TEST_KEY_1": "test_value_1",
        "TEST_KEY_2": "test_value_2",
        "TEST_KEY_3": "test_value_3",
    }

    # Update variables
    await repository.update(variables)

    # Get all variables
    all_variables = await repository.get_all()

    # Verify all variables are returned
    assert len(all_variables) == 3
    assert all_variables["TEST_KEY_1"] == variables["TEST_KEY_1"]
    assert all_variables["TEST_KEY_2"] == variables["TEST_KEY_2"]
    assert all_variables["TEST_KEY_3"] == variables["TEST_KEY_3"]
