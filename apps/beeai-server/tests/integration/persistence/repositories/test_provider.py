# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
from datetime import timedelta

import pytest
from a2a.types import AgentCapabilities, AgentCard
from sqlalchemy import UUID, text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration
from beeai_server.domain.models.provider import NetworkProviderLocation, Provider
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.provider import SqlAlchemyProviderRepository
from beeai_server.utils.utils import utc_now

pytestmark = pytest.mark.integration


@pytest.fixture
def set_di_configuration(override_global_dependency):
    # NetworkProviderLocation is using Configuration during validation
    with override_global_dependency(Configuration, Configuration()):
        yield


@pytest.fixture
async def test_provider(set_di_configuration, admin_user: UUID) -> Provider:
    """Create a test provider for use in tests."""
    source = NetworkProviderLocation(root="http://localhost:8000")
    return Provider(
        source=source,
        origin=source.origin,
        registry=None,
        agent_card=AgentCard(
            name="Hello World Agent",
            description="Just a hello world agent",
            url="http://localhost:8000/",
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(),
            skills=[],
        ),
        auto_stop_timeout=timedelta(minutes=5),
        created_by=admin_user,
    )


async def test_create_provider(db_transaction: AsyncConnection, test_provider: Provider):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(provider=test_provider)

    # Verify provider was created
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    row = result.fetchone()
    assert row is not None
    assert str(row.id) == str(test_provider.id)
    assert row.source == str(test_provider.source.root)
    assert row.registry == (str(test_provider.registry.root) if test_provider.registry else None)
    assert row.auto_stop_timeout_sec == int(test_provider.auto_stop_timeout.total_seconds())
    assert row.type == test_provider.type


@pytest.mark.usefixtures("set_di_configuration")
async def test_get_provider(db_transaction: AsyncConnection, test_provider, admin_user: UUID):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    source = NetworkProviderLocation(root="http://localhost:8000")
    provider_data = {
        "id": source.provider_id,
        "source": str(source.root),
        "registry": None,
        "created_at": utc_now(),
        "last_active_at": utc_now(),
        "agent_card": {
            "capabilities": {},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "description": "Just a hello world agent",
            "name": "Hello World Agent",
            "protocolVersion": "0.2.5",
            "skills": [],
            "url": "http://localhost:8000/",
            "version": "1.0.0",
        },
        "auto_stop_timeout_sec": 300,  # 5 minutes
        "type": "unmanaged",
        "version_info": {"docker": None, "github": None},
        "unmanaged_state": None,
        "created_by": admin_user,
    }

    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, type, source, origin, version_info, registry, auto_stop_timeout_sec, agent_card, created_at, updated_at, last_active_at, created_by, unmanaged_state) "
            "VALUES (:id, :type, :source, :origin, :version_info, :registry, :auto_stop_timeout_sec, :agent_card, :created_at, :updated_at, :last_active_at, :created_by, :unmanaged_state)"
        ),
        {
            **provider_data,
            "origin": source.origin,
            "updated_at": utc_now(),
            "agent_card": json.dumps(provider_data["agent_card"]),
            "version_info": json.dumps(provider_data["version_info"]),
        },
    )
    # Get provider
    provider = await repository.get(provider_id=provider_data["id"])

    # Verify provider
    assert provider.id == provider_data["id"]
    assert str(provider.source.root) == provider_data["source"]
    assert provider.registry is None
    assert provider.auto_stop_timeout == timedelta(seconds=provider_data["auto_stop_timeout_sec"])
    assert provider.type == provider_data["type"]


async def test_get_provider_not_found(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Try to get non-existent provider
    with pytest.raises(EntityNotFoundError):
        await repository.get(provider_id=uuid.uuid4())


async def test_delete_provider(db_transaction: AsyncConnection, test_provider: Provider):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(provider=test_provider)

    # Verify provider was created
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    assert result.fetchone() is not None

    # Delete provider
    await repository.delete(provider_id=test_provider.id)

    # Verify provider was deleted
    result = await db_transaction.execute(text("SELECT * FROM providers WHERE id = :id"), {"id": test_provider.id})
    assert result.fetchone() is None


@pytest.mark.usefixtures("set_di_configuration")
async def test_list_providers(db_transaction: AsyncConnection, admin_user: UUID):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)
    source = NetworkProviderLocation(root="http://localhost:8001")
    source2 = NetworkProviderLocation(root="http://localhost:8002")

    # Create providers
    first_provider = {
        "id": source.provider_id,
        "source": str(source.root),
        "registry": None,
        "created_at": utc_now(),
        "last_active_at": utc_now(),
        "agent_card": {
            "capabilities": {},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "description": "Test agent 1",
            "name": "Test Agent 1",
            "protocolVersion": "0.2.5",
            "skills": [],
            "url": "http://localhost:8001/",
            "version": "1.0.0",
        },
        "auto_stop_timeout_sec": 300,
        "type": "unmanaged",
        "version_info": {"docker": None, "github": None},
        "unmanaged_state": None,
        "created_by": admin_user,
    }
    second_provider = {
        "id": source2.provider_id,
        "source": str(source2.root),
        "registry": None,
        "created_at": utc_now(),
        "last_active_at": utc_now(),
        "agent_card": {
            "capabilities": {},
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "description": "Test agent 2",
            "name": "Test Agent 2",
            "protocolVersion": "0.2.5",
            "skills": [],
            "url": "http://localhost:8002/",
            "version": "1.0.0",
        },
        "auto_stop_timeout_sec": 600,
        "type": "unmanaged",
        "version_info": {"docker": None, "github": None},
        "unmanaged_state": None,
        "created_by": admin_user,
    }

    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, type, source, origin, version_info, registry, agent_card, created_at, updated_at, last_active_at, auto_stop_timeout_sec, created_by, unmanaged_state) "
            "VALUES (:id, :type, :source, :origin, :version_info, :registry, :agent_card, :created_at, :updated_at, :last_active_at, :auto_stop_timeout_sec, :created_by, :unmanaged_state)"
        ),
        [
            {
                **first_provider,
                "origin": source.origin,
                "updated_at": utc_now(),
                "agent_card": json.dumps(first_provider["agent_card"]),
                "version_info": json.dumps(first_provider["version_info"]),
            },
            {
                **second_provider,
                "origin": source2.origin,
                "updated_at": utc_now(),
                "agent_card": json.dumps(second_provider["agent_card"]),
                "version_info": json.dumps(second_provider["version_info"]),
            },
        ],
    )

    # List all providers
    providers = {provider.id: provider async for provider in repository.list()}

    # Verify providers
    assert len(providers) == 2
    assert str(providers[first_provider["id"]].source.root) == first_provider["source"]
    assert providers[first_provider["id"]].auto_stop_timeout == timedelta(
        seconds=first_provider["auto_stop_timeout_sec"]
    )
    assert providers[first_provider["id"]].type == first_provider["type"]

    assert str(providers[second_provider["id"]].source.root) == second_provider["source"]
    assert providers[second_provider["id"]].auto_stop_timeout == timedelta(
        seconds=second_provider["auto_stop_timeout_sec"]
    )
    assert providers[second_provider["id"]].type == second_provider["type"]


async def test_create_duplicate_provider(db_transaction: AsyncConnection, test_provider: Provider, admin_user: UUID):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(provider=test_provider)

    # Try to create provider with same source (will generate same ID)
    duplicate_source = NetworkProviderLocation(root="http://localhost:8000")  # Same source, will generate same ID
    duplicate_provider = Provider(
        source=duplicate_source,
        origin=duplicate_source.origin,
        registry=None,
        agent_card=test_provider.agent_card.model_copy(update={"name": "NEW_AGENT"}),
        auto_stop_timeout=timedelta(minutes=10),  # Different timeout
        created_by=admin_user,
    )

    # This should raise a DuplicateEntityError because the source is the same
    with pytest.raises(DuplicateEntityError):
        await repository.create(provider=duplicate_provider)
