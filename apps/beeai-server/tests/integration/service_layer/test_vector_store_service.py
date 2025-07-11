# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

import pytest
import pytest_asyncio

from beeai_server.bootstrap import setup_database_engine
from beeai_server.configuration import Configuration, VectorStoresConfiguration
from beeai_server.domain.models.user import User
from beeai_server.domain.models.vector_store import DocumentType, VectorStoreItem
from beeai_server.exceptions import InvalidVectorDimensionError, StorageCapacityExceededError
from beeai_server.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWorkFactory
from beeai_server.service_layer.services.vector_stores import VectorStoreService

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def low_limit_config():
    """Create a configuration with a very low storage limit for testing."""
    return Configuration(vector_stores=VectorStoresConfiguration(storage_limit_per_user_bytes=2000))


@pytest_asyncio.fixture
async def uow_factory(low_limit_config, clean_up):
    return SqlAlchemyUnitOfWorkFactory(setup_database_engine(low_limit_config), low_limit_config)


@pytest_asyncio.fixture
async def vector_store_service(uow_factory, low_limit_config):
    """Create a VectorStoreService with real transaction behavior."""
    return VectorStoreService(uow_factory, low_limit_config)


@pytest_asyncio.fixture
async def test_user(uow_factory) -> User:
    async with uow_factory() as uow:
        return await uow.users.get_by_email(email="user@beeai.dev")


@pytest_asyncio.fixture
async def large_vector_items():
    """Create vector items that will exceed the storage limit."""
    # Create items with large text content and embeddings to quickly exceed 1000 bytes
    large_text = "This is a very large text content that will help us exceed the storage limit. " * 20  # ~1600 chars
    return [
        VectorStoreItem(
            document_id="large_doc_001",
            document_type=DocumentType.external,
            text=large_text,
            embedding=[1.0] * 128,  # 128-dimensional vector
            metadata={"source": "test_large.txt", "type": "large"},
        ),
        VectorStoreItem(
            document_id="large_doc_002",
            document_type=DocumentType.external,
            text=large_text,
            embedding=[2.0] * 128,
            metadata={"source": "test_large2.txt", "type": "large"},
        ),
        VectorStoreItem(
            document_id="large_doc_003",
            document_type=DocumentType.external,
            text=large_text,
            embedding=[3.0] * 128,
            metadata={"source": "test_large3.txt", "type": "large"},
        ),
    ]


@pytest.mark.asyncio
async def test_vector_store_storage_limit_enforcement(
    vector_store_service: VectorStoreService, test_user: User, large_vector_items: list[VectorStoreItem]
):
    """Test that storage limit is properly enforced when adding items to vector store."""
    # Create a vector store
    vector_store = await vector_store_service.create(
        name="test-storage-limit", dimension=128, model_id="test_model", user=test_user
    )

    # Add the first item - this should succeed (within limit)
    await vector_store_service.add_items(vector_store_id=vector_store.id, items=[large_vector_items[0]], user=test_user)

    # Verify the vector store was created and has usage stats
    retrieved_store = await vector_store_service.get(vector_store_id=vector_store.id, user=test_user)
    assert retrieved_store.stats is not None
    assert retrieved_store.stats.usage_bytes > 0
    initial_usage = retrieved_store.stats.usage_bytes

    # Try to add more items that would exceed the limit - this should raise Error
    with pytest.raises(StorageCapacityExceededError):
        await vector_store_service.add_items(
            vector_store_id=vector_store.id,
            items=large_vector_items[1:],  # Add remaining 2 large items
            user=test_user,
        )

    # Verify that the usage didn't change after the failed addition
    retrieved_store_after = await vector_store_service.get(vector_store_id=vector_store.id, user=test_user)
    assert retrieved_store_after.stats.usage_bytes == initial_usage


@pytest.mark.asyncio
async def test_storage_limit_check_happens_after_size_estimation(
    vector_store_service: VectorStoreService, test_user: User, large_vector_items: list[VectorStoreItem]
):
    """Test that storage limit is checked after documents are upserted but before items are added to vector DB."""
    # Create a vector store
    vector_store = await vector_store_service.create(
        name="test-storage-limit-timing", dimension=128, model_id="test_model", user=test_user
    )

    # Try to add items that exceed the limit in one go
    with pytest.raises(StorageCapacityExceededError):
        await vector_store_service.add_items(
            vector_store_id=vector_store.id,
            items=large_vector_items,  # All 3 large items at once
            user=test_user,
        )

    # Verify that no items were added to the vector store
    # (the documents might be created but vector items should not be)
    documents = await vector_store_service.list_documents(vector_store_id=vector_store.id, user=test_user)
    assert len(documents) == 0, "No documents should be present after limit exceeded"

    search_results = await vector_store_service.search(
        vector_store_id=vector_store.id, query_vector=[1.0] * 128, limit=10, user=test_user
    )
    assert len(search_results) == 0, "No vector items should be present after limit exceeded"


@pytest.mark.asyncio
async def test_invalid_vector_dimension(vector_store_service: VectorStoreService, test_user: User):
    # Create a vector store
    vector_store = await vector_store_service.create(
        name="test-small-items", dimension=128, model_id="test_model", user=test_user
    )

    small_items = [
        VectorStoreItem(
            id=uuid4(),
            document_id="small_doc_001",
            document_type=DocumentType.external,
            text="Small text",  # Very small text
            embedding=[1.0] * 64,  # Smaller embedding
        )
    ]

    with pytest.raises(InvalidVectorDimensionError):
        await vector_store_service.add_items(vector_store_id=vector_store.id, items=small_items, user=test_user)
