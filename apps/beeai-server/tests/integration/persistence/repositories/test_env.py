# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid
from uuid import UUID

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration, PersistenceConfiguration
from beeai_server.domain.repositories.env import EnvStoreEntity
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.env import SqlAlchemyEnvVariableRepository
from beeai_server.utils.utils import utc_now

pytestmark = pytest.mark.integration


@pytest.fixture
def encryption_config() -> Configuration:
    """Create a test configuration with an encryption key."""
    # Generate a new Fernet key for testing
    config = Configuration(persistence=PersistenceConfiguration(encryption_key=Fernet.generate_key().decode()))
    return config


@pytest.fixture
async def provider_id(db_transaction: AsyncConnection) -> UUID:
    """Test provider ID with actual provider record in database."""
    provider_id = uuid.uuid4()
    # Create a minimal provider record to satisfy foreign key constraint
    await db_transaction.execute(
        text(
            """
            INSERT INTO providers (id, source, auto_stop_timeout_sec, auto_remove, created_at, last_active_at, agent_card)
            VALUES (:id, :source, :timeout, :auto_remove, :created_at, :last_active_at, :agent_card)
            """
        ),
        {
            "id": provider_id,
            "source": "test://provider",
            "timeout": 3600,
            "auto_remove": False,
            "created_at": utc_now(),
            "last_active_at": utc_now(),
            "agent_card": "{}",
        },
    )
    return provider_id


@pytest.fixture
async def model_provider_id(db_transaction: AsyncConnection) -> UUID:
    """Test model provider ID with actual model provider record in database."""
    model_provider_id = uuid.uuid4()
    # Create a minimal model_provider record to satisfy foreign key constraint
    await db_transaction.execute(
        text(
            """
            INSERT INTO model_providers (id, name, type, base_url, created_at)
            VALUES (:id, :name, :type, :base_url, :created_at)
            """
        ),
        {
            "id": model_provider_id,
            "name": "Test Model Provider",
            "type": "openai",
            "base_url": f"https://test-{model_provider_id}.example.com",
            "created_at": utc_now(),
        },
    )
    return model_provider_id


@pytest.mark.asyncio
async def test_update_and_get(db_transaction: AsyncConnection, encryption_config: Configuration, provider_id: UUID):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "TEST_KEY_1": "test_value_1",
        "TEST_KEY_2": "test_value_2",
    }

    # Update variables
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        variables=variables,
    )

    # Verify variables were created in the database (encrypted)
    result = await db_transaction.execute(
        text("SELECT * FROM variables WHERE provider_id = :provider_id"), {"provider_id": provider_id}
    )
    rows = result.fetchall()
    assert len(rows) == 2

    # Get variables
    value1 = await repository.get(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=provider_id, key="TEST_KEY_1")
    value2 = await repository.get(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=provider_id, key="TEST_KEY_2")

    # Verify values
    assert value1 == variables["TEST_KEY_1"]
    assert value2 == variables["TEST_KEY_2"]


@pytest.mark.asyncio
async def test_get_with_default(db_transaction: AsyncConnection, encryption_config: Configuration, provider_id: UUID):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Get non-existent variable with default
    value = await repository.get(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        key="NON_EXISTENT_KEY",
        default="default_value",
    )

    # Verify default value is returned
    assert value == "default_value"


@pytest.mark.asyncio
async def test_get_not_found(db_transaction: AsyncConnection, encryption_config: Configuration, provider_id: UUID):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Try to get non-existent variable without default
    with pytest.raises(EntityNotFoundError):
        await repository.get(
            parent_entity=EnvStoreEntity.PROVIDER,
            parent_entity_id=provider_id,
            key="NON_EXISTENT_KEY",
        )


@pytest.mark.asyncio
async def test_update_remove(db_transaction: AsyncConnection, encryption_config: Configuration, provider_id: UUID):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "TEST_KEY_1": "test_value_1",
        "TEST_KEY_2": "test_value_2",
    }

    # Update variables
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        variables=variables,
    )

    # Verify variables were created
    result = await db_transaction.execute(
        text("SELECT * FROM variables WHERE provider_id = :provider_id"), {"provider_id": provider_id}
    )
    assert len(result.fetchall()) == 2

    # Update with one variable set to None (should remove it)
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        variables={"TEST_KEY_1": None},
    )

    # Verify TEST_KEY_1 was removed
    result = await db_transaction.execute(
        text("SELECT * FROM variables WHERE key = 'TEST_KEY_1' AND provider_id = :provider_id"),
        {"provider_id": provider_id},
    )
    assert result.fetchone() is None

    # Verify TEST_KEY_2 still exists
    result = await db_transaction.execute(
        text("SELECT * FROM variables WHERE key = 'TEST_KEY_2' AND provider_id = :provider_id"),
        {"provider_id": provider_id},
    )
    assert result.fetchone() is not None


@pytest.mark.asyncio
async def test_get_all(db_transaction: AsyncConnection, encryption_config: Configuration, provider_id: UUID):
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "TEST_KEY_1": "test_value_1",
        "TEST_KEY_2": "test_value_2",
        "TEST_KEY_3": "test_value_3",
    }

    # Update variables
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        variables=variables,
    )

    # Get all variables
    all_variables = await repository.get_all(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_ids=[provider_id],
    )

    # Verify all variables are returned for the provider
    assert len(all_variables) == 1
    assert provider_id in all_variables
    provider_vars = all_variables[provider_id]
    assert len(provider_vars) == 3
    assert provider_vars["TEST_KEY_1"] == variables["TEST_KEY_1"]
    assert provider_vars["TEST_KEY_2"] == variables["TEST_KEY_2"]
    assert provider_vars["TEST_KEY_3"] == variables["TEST_KEY_3"]


@pytest.mark.asyncio
async def test_model_provider_entity(
    db_transaction: AsyncConnection, encryption_config: Configuration, model_provider_id: UUID
):
    """Test environment variables work with model_provider entity type."""
    # Create repository
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Test variables
    variables = {
        "MODEL_API_KEY": "test_key",
        "MODEL_BASE_URL": "https://api.example.com",
    }

    # Update variables for model provider
    await repository.update(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=model_provider_id,
        variables=variables,
    )

    # Get variables
    api_key = await repository.get(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=model_provider_id,
        key="MODEL_API_KEY",
    )
    base_url = await repository.get(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=model_provider_id,
        key="MODEL_BASE_URL",
    )

    # Verify values
    assert api_key == variables["MODEL_API_KEY"]
    assert base_url == variables["MODEL_BASE_URL"]


@pytest.mark.asyncio
async def test_variable_isolation_between_entities(
    db_transaction: AsyncConnection,
    encryption_config: Configuration,
    provider_id: UUID,
    model_provider_id: UUID,
):
    """Test that variables are isolated between different parent entities."""
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Add variables to provider
    provider_vars = {"API_KEY": "provider_key", "SHARED_VAR": "provider_value"}
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        variables=provider_vars,
    )

    # Add variables to model provider (same keys, different values)
    model_provider_vars = {"API_KEY": "model_provider_key", "SHARED_VAR": "model_provider_value"}
    await repository.update(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=model_provider_id,
        variables=model_provider_vars,
    )

    # Get variables from provider
    provider_api_key = await repository.get(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        key="API_KEY",
    )
    provider_shared = await repository.get(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider_id,
        key="SHARED_VAR",
    )

    # Get variables from model provider
    model_api_key = await repository.get(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=model_provider_id,
        key="API_KEY",
    )
    model_shared = await repository.get(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=model_provider_id,
        key="SHARED_VAR",
    )

    # Verify isolation - same keys have different values per entity
    assert provider_api_key == "provider_key"
    assert provider_shared == "provider_value"
    assert model_api_key == "model_provider_key"
    assert model_shared == "model_provider_value"


@pytest.mark.asyncio
async def test_get_all_multiple_entities(
    db_transaction: AsyncConnection,
    encryption_config: Configuration,
):
    """Test get_all method with multiple parent entities of the same type."""
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Create multiple provider IDs and their database records
    provider1_id = uuid.uuid4()
    provider2_id = uuid.uuid4()
    provider3_id = uuid.uuid4()

    # Create provider records in database
    for i, provider_id in enumerate([provider1_id, provider2_id, provider3_id], 1):
        await db_transaction.execute(
            text(
                """
                INSERT INTO providers (id, source, auto_stop_timeout_sec, auto_remove, created_at, last_active_at, agent_card)
                VALUES (:id, :source, :timeout, :auto_remove, :created_at, :last_active_at, :agent_card)
                """
            ),
            {
                "id": provider_id,
                "source": f"test://provider{i}",
                "timeout": 3600,
                "auto_remove": False,
                "created_at": utc_now(),
                "last_active_at": utc_now(),
                "agent_card": "{}",
            },
        )

    # Add variables to each provider
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider1_id,
        variables={"KEY1": "value1", "KEY2": "value2"},
    )

    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider2_id,
        variables={"KEY3": "value3", "KEY4": "value4"},
    )

    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=provider3_id,
        variables={"KEY5": "value5"},
    )

    # Get all variables for multiple providers
    all_variables = await repository.get_all(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_ids=[provider1_id, provider2_id, provider3_id],
    )

    # Verify results
    assert len(all_variables) == 3
    assert provider1_id in all_variables
    assert provider2_id in all_variables
    assert provider3_id in all_variables

    # Verify provider1 variables
    provider1_vars = all_variables[provider1_id]
    assert len(provider1_vars) == 2
    assert provider1_vars["KEY1"] == "value1"
    assert provider1_vars["KEY2"] == "value2"

    # Verify provider2 variables
    provider2_vars = all_variables[provider2_id]
    assert len(provider2_vars) == 2
    assert provider2_vars["KEY3"] == "value3"
    assert provider2_vars["KEY4"] == "value4"

    # Verify provider3 variables
    provider3_vars = all_variables[provider3_id]
    assert len(provider3_vars) == 1
    assert provider3_vars["KEY5"] == "value5"


@pytest.mark.asyncio
async def test_get_all_empty_ids_list(
    db_transaction: AsyncConnection,
    encryption_config: Configuration,
):
    """Test get_all method with empty parent entity IDs list."""
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)
    assert await repository.get_all(parent_entity=EnvStoreEntity.PROVIDER, parent_entity_ids=[]) == {}

    # Query for different nonexistent provider IDs
    nonexistent_id1 = uuid.uuid4()
    nonexistent_id2 = uuid.uuid4()

    all_variables = await repository.get_all(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_ids=[nonexistent_id1, nonexistent_id2],
    )

    # Should return empty dict since no variables exist for these IDs
    assert all_variables == {}


@pytest.mark.asyncio
async def test_variable_isolation_between_entity_types(
    db_transaction: AsyncConnection,
    encryption_config: Configuration,
):
    """Test that the same entity ID with different entity types are isolated."""
    repository = SqlAlchemyEnvVariableRepository(connection=db_transaction, configuration=encryption_config)

    # Use the same UUID for different entity types (this can happen in practice)
    entity_id = uuid.uuid4()

    # Create provider record
    await db_transaction.execute(
        text(
            """
            INSERT INTO providers (id, source, auto_stop_timeout_sec, auto_remove, created_at, last_active_at, agent_card)
            VALUES (:id, :source, :timeout, :auto_remove, :created_at, :last_active_at, :agent_card)
            """
        ),
        {
            "id": entity_id,
            "source": "test://provider",
            "timeout": 3600,
            "auto_remove": False,
            "created_at": utc_now(),
            "last_active_at": utc_now(),
            "agent_card": "{}",
        },
    )

    # Create model_provider record with the same UUID
    await db_transaction.execute(
        text(
            """
            INSERT INTO model_providers (id, name, type, base_url, created_at)
            VALUES (:id, :name, :type, :base_url, :created_at)
            """
        ),
        {
            "id": entity_id,
            "name": "Test Model Provider",
            "type": "openai",
            "base_url": f"https://test-{entity_id}.example.com",
            "created_at": utc_now(),
        },
    )

    # Add variables as provider entity
    await repository.update(
        parent_entity=EnvStoreEntity.PROVIDER,
        parent_entity_id=entity_id,
        variables={"SAME_KEY": "provider_value"},
    )

    # Add variables as model_provider entity (same UUID, different entity type)
    await repository.update(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER,
        parent_entity_id=entity_id,
        variables={"SAME_KEY": "model_provider_value"},
    )

    # Get variable as provider
    provider_value = await repository.get(
        parent_entity=EnvStoreEntity.PROVIDER, parent_entity_id=entity_id, key="SAME_KEY"
    )

    # Get variable as model_provider
    model_provider_value = await repository.get(
        parent_entity=EnvStoreEntity.MODEL_PROVIDER, parent_entity_id=entity_id, key="SAME_KEY"
    )

    # Values should be different despite same UUID
    assert provider_value == "provider_value"
    assert model_provider_value == "model_provider_value"
