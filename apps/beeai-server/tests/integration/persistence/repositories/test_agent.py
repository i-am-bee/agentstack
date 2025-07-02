# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json

import pytest
import pytest_asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text

from beeai_server.domain.models.agent import Agent, AcpMetadata
from beeai_server.exceptions import DuplicateEntityError, EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.agent import SqlAlchemyAgentRepository

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def test_provider(db_transaction) -> uuid.UUID:
    provider_id = uuid.uuid4()
    await db_transaction.execute(
        text(
            "INSERT INTO providers (id, source, registry, env, auto_stop_timeout_sec, auto_remove) "
            "VALUES (:id, :source, :registry, :env, :auto_stop_timeout, :auto_remove)"
        ),
        {
            "id": provider_id,
            "source": "local",
            "registry": "local",
            "env": "[]",
            "auto_stop_timeout": 10,
            "auto_remove": False,
        },
    )
    return provider_id


@pytest_asyncio.fixture
async def test_agent(db_transaction, test_provider: uuid.UUID):
    """Create a test agent for use in tests."""
    return Agent(
        name="Test Agent", description="A test agent", metadata=AcpMetadata(provider_id=test_provider, env=[], ui=None)
    )


@pytest.mark.asyncio
async def test_create_agent(db_transaction: AsyncConnection, test_agent: Agent):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    # Create agent
    await repository.bulk_create([test_agent])

    # Verify agent was created
    result = await db_transaction.execute(text("SELECT * FROM agents WHERE id = :id"), {"id": test_agent.id})
    row = result.fetchone()
    assert row is not None
    assert str(row.id) == str(test_agent.id)
    assert row.name == test_agent.name
    assert row.description == test_agent.description
    assert str(row.provider_id) == str(test_agent.metadata.provider_id)


@pytest.mark.asyncio
async def test_get_agent(db_transaction: AsyncConnection, test_provider):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    agent_data = {
        "id": uuid.uuid4(),
        "name": "Test Agent",
        "description": "A test agent",
        "provider_id": test_provider,
        "metadata": json.dumps({"provider_id": str(test_provider)}),
    }

    await db_transaction.execute(
        text(
            "INSERT INTO agents (id, name, description, provider_id, metadata) VALUES (:id, :name, :description, :provider_id, :metadata)"
        ),
        agent_data,
    )
    # Get agent
    agent = await repository.get_agent(agent_id=agent_data["id"])

    # Verify agent
    assert agent.id == agent_data["id"]
    assert agent.name == agent_data["name"]
    assert agent.description == agent_data["description"]
    assert agent.metadata.provider_id == agent_data["provider_id"]


@pytest.mark.asyncio
async def test_get_agent_not_found(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    # Try to get non-existent agent
    with pytest.raises(EntityNotFoundError):
        await repository.get_agent(agent_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_get_agent_by_name(db_transaction: AsyncConnection, test_agent):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    # Create agent
    await repository.bulk_create([test_agent])

    # Get agent by name
    agent = await repository.get_agent_by_name(name=test_agent.name)

    # Verify agent
    assert agent.id == test_agent.id
    assert agent.name == test_agent.name
    assert agent.description == test_agent.description
    assert agent.metadata.provider_id == test_agent.metadata.provider_id


@pytest.mark.asyncio
async def test_get_agent_by_name_not_found(db_transaction: AsyncConnection):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    # Try to get non-existent agent
    with pytest.raises(EntityNotFoundError):
        await repository.get_agent_by_name(name="Non-existent Agent")


@pytest.mark.asyncio
async def test_list_agents(db_transaction: AsyncConnection, test_provider):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    # Create agent
    first_agent = {
        "id": uuid.uuid4(),
        "name": "First Agent",
        "description": "first agent",
        "provider_id": test_provider,
        "metadata": json.dumps({"provider_id": str(test_provider)}),
    }
    second_agent = {
        "id": uuid.uuid4(),
        "name": "Second Agent",
        "description": "second agent",
        "provider_id": test_provider,
        "metadata": json.dumps({"provider_id": str(test_provider)}),
    }

    await db_transaction.execute(
        text(
            "INSERT INTO agents (id, name, description, provider_id, metadata) VALUES (:id, :name, :description, :provider_id, :metadata)"
        ),
        [first_agent, second_agent],
    )
    # List agents
    agents = {agent.id: agent async for agent in repository.list()}

    # Verify agents
    assert len(agents) == 2
    assert agents[first_agent["id"]].name == first_agent["name"]
    assert agents[first_agent["id"]].description == first_agent["description"]
    assert agents[first_agent["id"]].metadata.provider_id == first_agent["provider_id"]

    assert agents[second_agent["id"]].name == second_agent["name"]
    assert agents[second_agent["id"]].description == second_agent["description"]
    assert agents[second_agent["id"]].metadata.provider_id == second_agent["provider_id"]


@pytest.mark.asyncio
async def test_bulk_create_duplicate(db_transaction: AsyncConnection, test_agent):
    # Create repository
    repository = SqlAlchemyAgentRepository(connection=db_transaction)

    # Create agent
    await repository.bulk_create([test_agent])

    # Try to create agent with same name
    duplicate_agent = Agent(
        name=test_agent.name,  # Same name
        description="A duplicate agent",
        metadata=AcpMetadata(
            provider_id=uuid.uuid4(),
            env=[],
            ui=None,
        ),
    )

    # Verify duplicate error
    with pytest.raises(DuplicateEntityError):
        await repository.bulk_create([duplicate_agent])
