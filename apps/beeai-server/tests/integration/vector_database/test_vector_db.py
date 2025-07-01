# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
import pytest_asyncio
import uuid
from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import text

from beeai_server.domain.models.vector_store import VectorStoreItem, VectorStoreSearchResult
from beeai_server.infrastructure.vector_database.vector_db import VectorDatabaseRepository

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def vector_db_repository(db_transaction: AsyncConnection) -> VectorDatabaseRepository:
    """Create a VectorDatabaseRepository instance for testing."""
    return VectorDatabaseRepository(connection=db_transaction, schema_name="vector_db")


@pytest_asyncio.fixture
async def test_collection_id(db_transaction: AsyncConnection) -> UUID:
    """Generate a test collection ID."""
    return uuid.uuid4()


@pytest_asyncio.fixture
async def sample_vector_items(test_collection_id: UUID) -> List[VectorStoreItem]:
    """Create sample vector items for testing."""
    return [
        VectorStoreItem(
            id=uuid.uuid4(),
            document_id="doc_001",
            embedding=[1.0] * 128,
            text="The quick brown fox jumps over the lazy dog.",
            metadata={"source": "test_doc_1.txt", "chapter": "1"},
        ),
        VectorStoreItem(
            id=uuid.uuid4(),
            document_id="doc_001",
            embedding=[2.0] * 128,
            text="Artificial intelligence is revolutionizing technology.",
            metadata={"source": "test_doc_1.txt", "chapter": "2"},
        ),
        VectorStoreItem(
            id=uuid.uuid4(),
            document_id="doc_002",
            embedding=[3.0] * 128,
            text="Vector databases enable efficient similarity search.",
            metadata={"source": "test_doc_2.txt", "chapter": "1"},
        ),
    ]


@pytest.mark.asyncio
async def test_create_collection(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    db_transaction: AsyncConnection,
):
    """Test creating a new vector collection."""
    dimension = 128

    # Create collection
    await vector_db_repository.create_collection(test_collection_id, dimension)

    # Verify table was created
    result = await db_transaction.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'vector_db' AND tablename = 'collections_dim_128'")
    )
    assert result.fetchone() is not None


@pytest.mark.asyncio
async def test_create_collection_with_unsupported_dimension(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    db_transaction: AsyncConnection,
):
    """Test creating collection with unsupported dimension uses closest supported dimension."""
    dimension = 100  # Not in SUPPORTED_DIMENSIONS, should use 64 (largest <= 100)

    # Create collection
    await vector_db_repository.create_collection(test_collection_id, dimension)

    # Verify table was created with supported dimension (64)
    result = await db_transaction.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'vector_db' AND tablename = 'collections_dim_64'")
    )
    assert result.fetchone() is not None


@pytest.mark.asyncio
async def test_add_items_to_collection(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test adding vector items to a collection."""
    dimension = 128

    # Create collection first
    await vector_db_repository.create_collection(test_collection_id, dimension)

    # Add items to collection
    await vector_db_repository.add_items(test_collection_id, sample_vector_items)

    # Verify items were added
    result = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": test_collection_id},
    )
    count = result.scalar()
    assert count == len(sample_vector_items)

    # Verify specific item data
    result = await db_transaction.execute(
        text(
            "SELECT id, vector_store_document_id, text, metadata FROM vector_db.collections_dim_128 "
            "WHERE vector_store_id = :collection_id ORDER BY text"
        ),
        {"collection_id": test_collection_id},
    )
    rows = result.fetchall()

    assert len(rows) == 3
    assert rows[0].text == "Artificial intelligence is revolutionizing technology."
    assert rows[0].vector_store_document_id == "doc_001"
    assert rows[1].text == "The quick brown fox jumps over the lazy dog."
    assert rows[1].vector_store_document_id == "doc_001"
    assert rows[2].text == "Vector databases enable efficient similarity search."
    assert rows[2].vector_store_document_id == "doc_002"


@pytest.mark.asyncio
async def test_add_empty_items_list(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
):
    """Test adding empty items list does nothing."""
    dimension = 128

    # Create collection first
    await vector_db_repository.create_collection(test_collection_id, dimension)

    # Add empty items list
    await vector_db_repository.add_items(test_collection_id, [])

    # This should not raise an error and should complete successfully


@pytest.mark.asyncio
async def test_estimate_size(
    vector_db_repository: VectorDatabaseRepository,
    sample_vector_items: List[VectorStoreItem],
):
    """Test size estimation for vector items."""
    document_info = vector_db_repository.estimate_size(sample_vector_items)

    # Should have 2 documents (doc_001 and doc_002)
    assert len(document_info) == 2

    # Check document IDs
    document_ids = {info.id for info in document_info}
    assert document_ids == {"doc_001", "doc_002"}

    # Check that all documents have positive usage_bytes
    for info in document_info:
        assert info.usage_bytes > 0

    # doc_001 should have larger usage_bytes (has 2 items vs 1 for doc_002)
    doc_001_info = next(info for info in document_info if info.id == "doc_001")
    doc_002_info = next(info for info in document_info if info.id == "doc_002")
    assert doc_001_info.usage_bytes > doc_002_info.usage_bytes


@pytest.mark.asyncio
async def test_similarity_search(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test similarity search functionality."""
    dimension = 128

    # Create collection and add items
    await vector_db_repository.create_collection(test_collection_id, dimension)
    await vector_db_repository.add_items(test_collection_id, sample_vector_items)

    # Perform similarity search with query vector closest to first item
    query_vector = [1.1] * 128  # Closest to [1.0] * 128
    results = await vector_db_repository.similarity_search(test_collection_id, query_vector, limit=2)

    # Convert to list for easier testing
    results_list = list(results)

    # Should return 2 results (limit=2)
    assert len(results_list) == 2

    # Each result should be a VectorStoreSearchResult with item and score
    for result in results_list:
        assert isinstance(result, VectorStoreSearchResult)
        assert hasattr(result, "item")
        assert hasattr(result, "score")
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0

    # First result should be closest to query vector
    first_result = results_list[0]
    assert first_result.item.text == "The quick brown fox jumps over the lazy dog."
    assert first_result.item.document_id == "doc_001"
    assert first_result.item.embedding == [1.0] * 128

    # First result should have highest score
    assert first_result.score >= results_list[1].score


@pytest.mark.asyncio
async def test_similarity_search_with_limit(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test similarity search with different limits."""
    dimension = 128

    # Create collection and add items
    await vector_db_repository.create_collection(test_collection_id, dimension)
    await vector_db_repository.add_items(test_collection_id, sample_vector_items)

    query_vector = [1.0] * 128

    # Test limit=1
    results = await vector_db_repository.similarity_search(test_collection_id, query_vector, limit=1)
    results_list = list(results)
    assert len(results_list) == 1
    assert isinstance(results_list[0], VectorStoreSearchResult)

    # Test limit=10 (more than available items)
    results = await vector_db_repository.similarity_search(test_collection_id, query_vector, limit=10)
    results_list = list(results)
    assert len(results_list) == 3  # Only 3 items available
    for result in results_list:
        assert isinstance(result, VectorStoreSearchResult)


@pytest.mark.asyncio
async def test_delete_documents(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test deleting documents from collection."""
    dimension = 128

    # Create collection and add items
    await vector_db_repository.create_collection(test_collection_id, dimension)
    await vector_db_repository.add_items(test_collection_id, sample_vector_items)

    # Verify all items are present
    result = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": test_collection_id},
    )
    assert result.scalar() == 3

    # Delete documents for doc_001
    await vector_db_repository.delete_documents(test_collection_id, dimension, ["doc_001"])

    # Verify doc_001 items are deleted
    result = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": test_collection_id},
    )
    assert result.scalar() == 1  # Only doc_002 item remains

    # Verify remaining item is from doc_002
    result = await db_transaction.execute(
        text(
            "SELECT vector_store_document_id FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"
        ),
        {"collection_id": test_collection_id},
    )
    remaining_doc_id = result.scalar()
    assert remaining_doc_id == "doc_002"


@pytest.mark.asyncio
async def test_delete_multiple_documents(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test deleting multiple documents at once."""
    dimension = 128

    # Create collection and add items
    await vector_db_repository.create_collection(test_collection_id, dimension)
    await vector_db_repository.add_items(test_collection_id, sample_vector_items)

    # Delete both documents
    await vector_db_repository.delete_documents(test_collection_id, dimension, ["doc_001", "doc_002"])

    # Verify all items are deleted
    result = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": test_collection_id},
    )
    assert result.scalar() == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_documents(
    vector_db_repository: VectorDatabaseRepository,
    test_collection_id: UUID,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test deleting non-existent documents doesn't affect existing data."""
    dimension = 128

    # Create collection and add items
    await vector_db_repository.create_collection(test_collection_id, dimension)
    await vector_db_repository.add_items(test_collection_id, sample_vector_items)

    # Try to delete non-existent document
    await vector_db_repository.delete_documents(test_collection_id, dimension, ["nonexistent_doc"])

    # Verify all original items are still present
    result = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": test_collection_id},
    )
    assert result.scalar() == 3


@pytest.mark.asyncio
async def test_multiple_collections_same_dimension(
    vector_db_repository: VectorDatabaseRepository,
    sample_vector_items: List[VectorStoreItem],
    db_transaction: AsyncConnection,
):
    """Test multiple collections using the same dimension share the same table."""
    dimension = 128
    collection_1 = uuid.uuid4()
    collection_2 = uuid.uuid4()

    # Create two collections with same dimension
    await vector_db_repository.create_collection(collection_1, dimension)
    await vector_db_repository.create_collection(collection_2, dimension)

    # Add items to both collections
    await vector_db_repository.add_items(collection_1, sample_vector_items[:2])
    await vector_db_repository.add_items(collection_2, sample_vector_items[2:])

    # Verify both collections have their items
    result_1 = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": collection_1},
    )
    assert result_1.scalar() == 2

    result_2 = await db_transaction.execute(
        text("SELECT COUNT(*) FROM vector_db.collections_dim_128 WHERE vector_store_id = :collection_id"),
        {"collection_id": collection_2},
    )
    assert result_2.scalar() == 1

    # Verify total items across both collections
    total_result = await db_transaction.execute(text("SELECT COUNT(*) FROM vector_db.collections_dim_128"))
    assert total_result.scalar() == 3


@pytest.mark.asyncio
async def test_different_dimensions_use_different_tables(
    vector_db_repository: VectorDatabaseRepository,
    db_transaction: AsyncConnection,
):
    """Test that different dimensions create different tables."""
    collection_128 = uuid.uuid4()
    collection_256 = uuid.uuid4()

    # Create collections with different dimensions
    await vector_db_repository.create_collection(collection_128, 128)
    await vector_db_repository.create_collection(collection_256, 256)

    # Verify both tables exist
    result = await db_transaction.execute(
        text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'vector_db' "
            "AND tablename IN ('collections_dim_128', 'collections_dim_256') ORDER BY tablename"
        )
    )
    tables = [row.tablename for row in result.fetchall()]
    assert tables == ["collections_dim_128", "collections_dim_256"]


@pytest.mark.asyncio
async def test_dimension_mapping_to_supported_dimensions(
    vector_db_repository: VectorDatabaseRepository,
):
    """Test that dimensions are mapped to supported dimensions correctly."""
    # Test various dimension mappings - function returns highest supported dimension <= input
    # For inputs smaller than minimum supported, it returns the minimum supported dimension
    test_cases = [
        (50, 64),  # 50 -> 64 (minimum supported dimension, since 50 < 64)
        (64, 64),  # 64 -> 64 (exact match)
        (100, 64),  # 100 -> 64 (largest supported <= 100)
        (128, 128),  # 128 -> 128 (exact match)
        (200, 128),  # 200 -> 128 (largest supported <= 200)
        (1000, 896),  # 1000 -> 896 (largest supported <= 1000)
        (5000, 4000),  # 5000 -> 4000 (highest supported)
    ]

    for input_dim, expected_dim in test_cases:
        mapped_dim = vector_db_repository._get_supported_dimension(input_dim)
        assert mapped_dim == expected_dim, f"Input {input_dim} should map to {expected_dim}, got {mapped_dim}"


@pytest.mark.asyncio
async def test_get_item_size_calculation(
    vector_db_repository: VectorDatabaseRepository,
    sample_vector_items: List[VectorStoreItem],
):
    """Test item size calculation is consistent and reasonable."""
    item = sample_vector_items[0]
    size = vector_db_repository._get_item_size(item)

    # Size should be positive
    assert size > 0

    # Size should be reasonable (not too small, not too large)
    assert 100 < size < 10000  # Reasonable range for text + embedding + metadata

    # Different items should have different sizes
    sizes = [vector_db_repository._get_item_size(item) for item in sample_vector_items]
    assert len(set(sizes)) > 1  # At least some items should have different sizes
