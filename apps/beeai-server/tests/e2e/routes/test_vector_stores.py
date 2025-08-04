# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from beeai_sdk.platform.vector_store import VectorStore, VectorStoreItem

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_vector_stores(subtests, api_client):
    items = [
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="The quick brown fox jumps over the lazy dog.",
            embedding=[1.0] * 127 + [4.0],
            metadata={"source": "document_a.txt", "chapter": "1"},
        ),
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="Artificial intelligence is transforming industries.",
            embedding=[1.0] * 127 + [3.0],
            metadata={"source": "document_a.txt", "chapter": "2"},
        ),
        VectorStoreItem(
            document_id="doc_003",
            document_type="external",
            model_id="custom_model_id",
            text="Vector databases are optimized for similarity searches.",
            embedding=[1.0] * 127 + [2.0],
            metadata=None,
        ),
    ]

    with subtests.test("create a vector store"):
        vector_store = await VectorStore.create(
            name="test-vector-store",
            dimension=128,
            model_id="custom_model_id",
            client=api_client,
        )

    with subtests.test("upload vectors"):
        await vector_store.add_documents(items, client=api_client)

    with subtests.test("verify usage_bytes updated after upload"):
        await vector_store.get(client=api_client)
        usage_bytes = vector_store.stats.usage_bytes if vector_store.stats else 0
        assert usage_bytes > 0, "Usage bytes should be greater than 0 after uploading vectors"

    with subtests.test("search vectors"):
        search_results = await vector_store.search(query_vector=[1.0] * 127 + [1.0], client=api_client)

        # Check that each result has the new structure with item and score
        for result in search_results:
            assert hasattr(result, "item")
            assert hasattr(result, "score")
            assert isinstance(result.score, (int, float))
            assert 0.0 <= result.score <= 1.0

        # Verify the search results order based on the items in the result
        assert search_results[0].item.embedding == items[2].embedding
        assert search_results[1].item.embedding == items[1].embedding
        assert search_results[2].item.embedding == items[0].embedding


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_vector_store_deletion(subtests, api_client):
    """Test vector store deletion functionality"""
    items = [
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="Sample text for deletion test.",
            embedding=[1.0] * 128,
            metadata={"source": "test.txt"},
        )
    ]

    with subtests.test("create vector store for deletion test"):
        vector_store = await VectorStore.create(
            name="test-deletion-store",
            dimension=128,
            model_id="custom_model_id",
            client=api_client,
        )
        vector_store_id = vector_store.id

    with subtests.test("add items to vector store"):
        await vector_store.add_documents(items, client=api_client)

    with subtests.test("verify vector store exists before deletion"):
        await vector_store.get(client=api_client)
        assert vector_store.id == vector_store_id

    with subtests.test("delete vector store"):
        await vector_store.delete(client=api_client)

    with subtests.test("verify vector store is deleted"):
        with pytest.raises(Exception):  # Should raise an exception for 404
            await VectorStore.get(str(vector_store_id), client=api_client)


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_document_deletion(subtests, api_client):
    """Test individual document deletion functionality"""
    initial_items = [
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="First document text.",
            embedding=[1.0] * 127 + [1.0],
            metadata={"source": "doc1.txt"},
        ),
        VectorStoreItem(
            document_id="doc_002",
            document_type="external",
            model_id="custom_model_id",
            text="Second document text.",
            embedding=[1.0] * 127 + [2.0],
            metadata={"source": "doc2.txt"},
        ),
        VectorStoreItem(
            document_id="doc_003",
            document_type="external",
            model_id="custom_model_id",
            text="Third document text.",
            embedding=[1.0] * 127 + [3.0],
            metadata={"source": "doc3.txt"},
        ),
    ]

    with subtests.test("create vector store"):
        vector_store = await VectorStore.create(
            name="test-doc-deletion",
            dimension=128,
            model_id="custom_model_id",
            client=api_client,
        )

    with subtests.test("add initial documents"):
        await vector_store.add_documents(initial_items, client=api_client)

    with subtests.test("verify all documents exist via search and track usage_bytes"):
        search_results = await vector_store.search(query_vector=[1.0] * 128, limit=10, client=api_client)
        assert len(search_results) == 3

        await vector_store.get(client=api_client)
        usage_bytes_before_deletion = vector_store.stats.usage_bytes if vector_store.stats else 0
        assert usage_bytes_before_deletion > 0, "Usage bytes should be greater than 0 after adding documents"

    with subtests.test("delete specific document"):
        await vector_store.delete_document("doc_002", client=api_client)

    with subtests.test("verify document was deleted and usage_bytes decreased"):
        search_results = await vector_store.search(query_vector=[1.0] * 128, limit=10, client=api_client)
        assert len(search_results) == 2
        document_ids = [result.item.document_id for result in search_results]
        assert "doc_002" not in document_ids
        assert "doc_001" in document_ids
        assert "doc_003" in document_ids

        await vector_store.get(client=api_client)
        usage_bytes_after_deletion = vector_store.stats.usage_bytes if vector_store.stats else 0
        assert usage_bytes_after_deletion < usage_bytes_before_deletion, (
            "Usage bytes should decrease after deleting a document"
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_adding_items_to_existing_documents(subtests, api_client):
    """Test adding new items to existing documents in vector store"""
    initial_items = [
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="Initial content for document 1.",
            embedding=[1.0] * 127 + [1.0],
            metadata={"source": "doc1.txt", "chapter": "1"},
        ),
        VectorStoreItem(
            document_id="doc_002",
            document_type="external",
            model_id="custom_model_id",
            text="Initial content for document 2.",
            embedding=[1.0] * 127 + [2.0],
            metadata={"source": "doc2.txt", "chapter": "1"},
        ),
    ]

    additional_items = [
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="Additional content for document 1.",
            embedding=[1.0] * 127 + [1.5],
            metadata={"source": "doc1.txt", "chapter": "2"},
        ),
        VectorStoreItem(
            document_id="doc_003",
            document_type="external",
            model_id="custom_model_id",
            text="New document 3 content.",
            embedding=[1.0] * 127 + [3.0],
            metadata={"source": "doc3.txt", "chapter": "1"},
        ),
    ]

    with subtests.test("create vector store"):
        vector_store = await VectorStore.create(
            name="test-add-items",
            dimension=128,
            model_id="custom_model_id",
            client=api_client,
        )

    with subtests.test("verify initial vector store usage_bytes is 0"):
        await vector_store.get(client=api_client)
        initial_usage_bytes = vector_store.stats.usage_bytes if vector_store.stats else 0
        assert initial_usage_bytes == 0

    with subtests.test("add initial items"):
        await vector_store.add_documents(initial_items, client=api_client)

    with subtests.test("verify initial items count and usage_bytes updated"):
        search_results = await vector_store.search(query_vector=[1.0] * 128, limit=10, client=api_client)
        assert len(search_results) == 2

        await vector_store.get(client=api_client)
        usage_bytes_after_initial = vector_store.stats.usage_bytes if vector_store.stats else 0
        assert usage_bytes_after_initial > 0, "Usage bytes should be greater than 0 after adding items"

    with subtests.test("add additional items to existing and new documents"):
        await vector_store.add_documents(additional_items, client=api_client)

    with subtests.test("verify all items are present and usage_bytes increased"):
        search_results = await vector_store.search(query_vector=[1.0] * 128, limit=10, client=api_client)
        assert len(search_results) == 4

        await vector_store.get(client=api_client)
        usage_bytes_after_additional = vector_store.stats.usage_bytes if vector_store.stats else 0
        assert usage_bytes_after_additional > usage_bytes_after_initial, (
            "Usage bytes should increase after adding more items"
        )

    with subtests.test("verify document 1 has multiple items"):
        doc_001_items = [result for result in search_results if result.item.document_id == "doc_001"]
        assert len(doc_001_items) == 2
        chapters = {result.item.metadata["chapter"] for result in doc_001_items if result.item.metadata}
        assert chapters == {"1", "2"}

    with subtests.test("verify new document was created"):
        doc_003_items = [result for result in search_results if result.item.document_id == "doc_003"]
        assert len(doc_003_items) == 1
        assert doc_003_items[0].item.text == "New document 3 content."


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_document_listing(subtests, api_client):
    """Test listing documents in a vector store"""
    items = [
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="Content for document 1.",
            embedding=[1.0] * 128,
            metadata={"source": "doc1.txt"},
        ),
        VectorStoreItem(
            document_id="doc_001",
            document_type="external",
            model_id="custom_model_id",
            text="More content for document 1.",
            embedding=[2.0] * 128,
            metadata={"source": "doc1.txt"},
        ),
        VectorStoreItem(
            document_id="doc_002",
            document_type="external",
            model_id="custom_model_id",
            text="Content for document 2.",
            embedding=[3.0] * 128,
            metadata={"source": "doc2.txt"},
        ),
    ]

    with subtests.test("create vector store"):
        vector_store = await VectorStore.create(
            name="test-doc-listing",
            dimension=128,
            model_id="custom_model_id",
            client=api_client,
        )

    with subtests.test("add items to vector store"):
        await vector_store.add_documents(items, client=api_client)

    with subtests.test("list documents in vector store"):
        assert {doc.id for doc in await vector_store.list_documents(client=api_client)} == {"doc_001", "doc_002"}
