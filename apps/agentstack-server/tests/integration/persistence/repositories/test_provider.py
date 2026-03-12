# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import uuid

import pytest
from a2a.types import AgentCapabilities, AgentCard
from sqlalchemy import UUID, text
from sqlalchemy.ext.asyncio import AsyncConnection

from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.provider import NetworkProviderLocation, Provider
from agentstack_server.exceptions import DuplicateEntityError, EntityNotFoundError
from agentstack_server.infrastructure.persistence.repositories.provider import SqlAlchemyProviderRepository
from agentstack_server.utils.utils import utc_now

pytestmark = pytest.mark.integration


@pytest.fixture
def set_di_configuration(override_global_dependency):
    # NetworkProviderLocation is using Configuration during validation
    with override_global_dependency(Configuration, Configuration()):
        yield


@pytest.fixture
async def test_provider(set_di_configuration, normal_user: UUID) -> Provider:
    """Create a test provider for use in tests."""
    source = NetworkProviderLocation(root="http://localhost:8000")
    return Provider(
        source=source,
        origin=source.origin,
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
        created_by=normal_user,
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
    assert row.source_type == test_provider.source_type


@pytest.mark.usefixtures("set_di_configuration")
async def test_get_provider(db_transaction: AsyncConnection, test_provider, normal_user: UUID):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    source = NetworkProviderLocation(root="http://localhost:8000")
    provider_data = {
        "id": source.provider_id,
        "source": str(source.root),
        "source_type": "api",
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
        "state": None,
        "created_by": normal_user,
    }

    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, source, source_type, origin, agent_card, created_at, updated_at, last_active_at, created_by, state) "
            "VALUES (:id, :source, :source_type, :origin, :agent_card, :created_at, :updated_at, :last_active_at, :created_by, :state)"
        ),
        {
            **provider_data,
            "origin": source.origin,
            "updated_at": utc_now(),
            "agent_card": json.dumps(provider_data["agent_card"]),
        },
    )
    # Get provider
    provider = await repository.get(provider_id=provider_data["id"])

    # Verify provider
    assert provider.id == provider_data["id"]
    assert str(provider.source.root) == provider_data["source"]
    assert provider.source_type == provider_data["source_type"]
    assert provider.state is None


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
async def test_list_providers(db_transaction: AsyncConnection, normal_user: UUID):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)
    source = NetworkProviderLocation(root="http://localhost:8001")
    source2 = NetworkProviderLocation(root="http://localhost:8002")

    # Create providers
    first_provider = {
        "id": source.provider_id,
        "source": str(source.root),
        "source_type": "api",
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
        "state": None,
        "created_by": normal_user,
    }
    second_provider = {
        "id": source2.provider_id,
        "source": str(source2.root),
        "source_type": "api",
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
        "state": None,
        "created_by": normal_user,
    }

    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, source, source_type, origin, agent_card, created_at, updated_at, last_active_at, created_by, state) "
            "VALUES (:id, :source, :source_type, :origin, :agent_card, :created_at, :updated_at, :last_active_at, :created_by, :state)"
        ),
        [
            {
                **first_provider,
                "origin": source.origin,
                "updated_at": utc_now(),
                "agent_card": json.dumps(first_provider["agent_card"]),
            },
            {
                **second_provider,
                "origin": source2.origin,
                "updated_at": utc_now(),
                "agent_card": json.dumps(second_provider["agent_card"]),
            },
        ],
    )

    # List all providers
    providers = {provider.id: provider async for provider in repository.list()}

    # Verify providers
    assert len(providers) == 2
    assert str(providers[first_provider["id"]].source.root) == first_provider["source"]
    assert providers[first_provider["id"]].source_type == first_provider["source_type"]

    assert str(providers[second_provider["id"]].source.root) == second_provider["source"]
    assert providers[second_provider["id"]].source_type == second_provider["source_type"]


async def test_create_duplicate_provider(db_transaction: AsyncConnection, test_provider: Provider, normal_user: UUID):
    # Create repository
    repository = SqlAlchemyProviderRepository(connection=db_transaction)

    # Create provider
    await repository.create(provider=test_provider)

    # Try to create provider with same source (will generate same ID)
    duplicate_source = NetworkProviderLocation(root="http://localhost:8000")  # Same source, will generate same ID
    duplicate_provider = Provider(
        source=duplicate_source,
        origin=duplicate_source.origin,
        agent_card=test_provider.agent_card.model_copy(update={"name": "NEW_AGENT"}),
        created_by=normal_user,
    )

    # This should raise a DuplicateEntityError because the source is the same
    with pytest.raises(DuplicateEntityError):
        await repository.create(provider=duplicate_provider)
