# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
from datetime import timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import Provider, NetworkProviderLocation, EnvVar
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.provider import SqlAlchemyProviderRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def set_di_configuration(override_global_dependency):
    # NetworkProviderLocation is using Configuration during validation
    with override_global_dependency(Configuration, Configuration()):
        yield


@pytest_asyncio.fixture
async def test_provider(set_di_configuration) -> Provider:
    """Create a test provider for use in tests."""
    return Provider(
        source=NetworkProviderLocation(root="http://localhost:8000"),
        registry=None,
        env=[
            EnvVar(name="TEST_ENV", description="Test environment variable", required=False),
        ],
        auto_stop_timeout=timedelta(minutes=5),
        auto_remove=False,
    )


@pytest.mark.asyncio
async def test_create_provider(db_transaction: AsyncConnection, test_provider: Provider):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(test_provider)

    # Verify provider was created
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    row = result.fetchone()
    assert row is not None
    assert str(row.id) == str(test_provider.id)
    assert row.source == str(test_provider.source.root)
    assert row.registry == (str(test_provider.registry.root) if test_provider.registry else None)
    assert row.auto_stop_timeout_sec == int(test_provider.auto_stop_timeout.total_seconds())
    assert row.auto_remove == test_provider.auto_remove


@pytest.mark.asyncio
@pytest.mark.usefixtures("set_di_configuration")
async def test_get_provider(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    source = NetworkProviderLocation(root="http://localhost:8000")
    provider_data = {
        "id": source.provider_id,
        "source": str(source.root),
        "registry": None,
        "env": json.dumps([{"name": "TEST_ENV", "description": "Test environment variable", "required": False}]),
        "auto_stop_timeout_sec": 300,  # 5 minutes
        "auto_remove": False,
    }

    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, source, registry, env, auto_stop_timeout_sec, auto_remove) "
            "VALUES (:id, :source, :registry, :env, :auto_stop_timeout_sec, :auto_remove)"
        ),
        provider_data,
    )
    # Get provider
    provider = await repository.get(provider_id=provider_data["id"])

    # Verify provider
    assert provider.id == provider_data["id"]
    assert str(provider.source.root) == provider_data["source"]
    assert provider.registry is None
    assert provider.auto_stop_timeout == timedelta(seconds=provider_data["auto_stop_timeout_sec"])
    assert provider.auto_remove == provider_data["auto_remove"]


@pytest.mark.asyncio
async def test_get_provider_not_found(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Try to get non-existent provider
    with pytest.raises(EntityNotFoundError):
        await repository.get(provider_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_delete_provider(db_transaction: AsyncConnection, test_provider: Provider):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(test_provider)

    # Verify provider was created
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    assert result.fetchone() is not None

    # Delete provider
    await repository.delete(provider_id=test_provider.id)

    # Verify provider was deleted
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    assert result.fetchone() is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("set_di_configuration")
async def test_list_providers(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)
    source = NetworkProviderLocation(root="http://localhost:8001")
    source2 = NetworkProviderLocation(root="http://localhost:8002")

    # Create providers
    first_provider = {
        "id": source.provider_id,
        "source": str(source.root),
        "registry": None,
        "env": json.dumps([{"name": "TEST_ENV_1", "description": "Test environment variable 1", "required": False}]),
        "auto_stop_timeout_sec": 300,
        "auto_remove": False,
    }
    second_provider = {
        "id": source2.provider_id,
        "source": str(source2.root),
        "registry": None,
        "env": json.dumps([{"name": "TEST_ENV_2", "description": "Test environment variable 2", "required": False}]),
        "auto_stop_timeout_sec": 600,
        "auto_remove": True,
    }

    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, source, registry, env, auto_stop_timeout_sec, auto_remove) "
            "VALUES (:id, :source, :registry, :env, :auto_stop_timeout_sec, :auto_remove)"
        ),
        [first_provider, second_provider],
    )

    # List all providers
    providers = {provider.id: provider async for provider in repository.list()}

    # Verify providers
    assert len(providers) == 2
    assert str(providers[first_provider["id"]].source.root) == first_provider["source"]
    assert providers[first_provider["id"]].auto_stop_timeout == timedelta(
        seconds=first_provider["auto_stop_timeout_sec"]
    )
    assert providers[first_provider["id"]].auto_remove == first_provider["auto_remove"]

    assert str(providers[second_provider["id"]].source.root) == second_provider["source"]
    assert providers[second_provider["id"]].auto_stop_timeout == timedelta(
        seconds=second_provider["auto_stop_timeout_sec"]
    )
    assert providers[second_provider["id"]].auto_remove == second_provider["auto_remove"]

    # List providers with auto_remove filter
    auto_remove_providers = {provider.id: provider async for provider in repository.list(auto_remove_filter=True)}
    assert len(auto_remove_providers) == 1
    assert second_provider["id"] in auto_remove_providers

    # List providers with auto_remove=False filter
    non_auto_remove_providers = {provider.id: provider async for provider in repository.list(auto_remove_filter=False)}
    assert len(non_auto_remove_providers) == 1
    assert first_provider["id"] in non_auto_remove_providers


@pytest.mark.asyncio
async def test_create_duplicate_provider(db_transaction: AsyncConnection, test_provider: Provider):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(test_provider)

    # Try to create provider with same ID (should succeed with auto_remove=False)
    duplicate_provider = Provider(
        source=NetworkProviderLocation(root="http://localhost:8000"),  # Same source, will generate same ID
        registry=None,
        env=[EnvVar(name="DIFFERENT_ENV", description="Different environment variable")],
        auto_stop_timeout=timedelta(minutes=10),  # Different timeout
        auto_remove=False,
    )

    # This should raise a DuplicateEntityError because the source is the same
    with pytest.raises(DuplicateEntityError):
        await repository.create(duplicate_provider)


@pytest.mark.asyncio
async def test_replace_transient_provider(db_transaction: AsyncConnection, test_provider: Provider):
    repository = SqlAlchemyProviderRepository(connection=db_transaction)
    # Create provider with auto_remove=True (should succeed by replacing the existing one)

    test_provider.auto_remove = True  # This should allow replacement
    await repository.create(test_provider)
    new_provider = Provider(
        source=NetworkProviderLocation(root="http://localhost:8000"),  # Same source will generate same ID
        env=[EnvVar(name="NEW_ENV", description="different env")],
        auto_remove=True,
    )

    # This should succeed
    await repository.create(new_provider)

    # Verify provider was updated
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    row = result.fetchone()
    assert row is not None
    assert row.env[0]["name"] == "NEW_ENV"
