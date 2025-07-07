# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_vector_stores(subtests, api_client, acp_client):
    items = [
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "The quick brown fox jumps over the lazy dog.",
            "embedding": [1.0] * 127 + [4.0],
            "metadata": {"source": "document_a.txt", "chapter": "1"},
        },
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Artificial intelligence is transforming industries.",
            "embedding": [1.0] * 127 + [3.0],
            "metadata": {"source": "document_a.txt", "chapter": "2"},
        },
        {
            "document_id": "doc_003",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Vector databases are optimized for similarity searches.",
            "embedding": [1.0] * 127 + [2.0],
            "metadata": None,
        },
    ]

    with subtests.test("create a vector store"):
        response = await api_client.post(
            "vector_stores", json={"name": "test-vector-store", "dimension": 128, "model_id": "custom_model_id"}
        )
        response.raise_for_status()
        vector_store_id = response.json()["id"]

    with subtests.test("upload vectors"):
        response = await api_client.put(f"vector_stores/{vector_store_id}", json=items)
        response.raise_for_status()

    with subtests.test("verify usage_bytes updated after upload"):
        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        vector_store = response.json()
        usage_bytes = vector_store.get("stats", {}).get("usage_bytes", 0)
        assert usage_bytes > 0, "Usage bytes should be greater than 0 after uploading vectors"

    with subtests.test("search vectors"):
        response = await api_client.post(
            f"vector_stores/{vector_store_id}/search",
            json={"query_vector": [1.0] * 127 + [1.0]},
        )
        response.raise_for_status()
        response_json = response.json()

        # Check that each item has the new structure with item and score
        for result in response_json["items"]:
            assert "item" in result
            assert "score" in result
            assert isinstance(result["score"], (int, float))
            assert 0.0 <= result["score"] <= 1.0

        # Verify the search results order based on the items in the result
        assert response_json["items"][0]["item"]["embedding"] == items[2]["embedding"]
        assert response_json["items"][1]["item"]["embedding"] == items[1]["embedding"]
        assert response_json["items"][2]["item"]["embedding"] == items[0]["embedding"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_vector_store_deletion(subtests, api_client, acp_client):
    """Test vector store deletion functionality"""
    items = [
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Sample text for deletion test.",
            "embedding": [1.0] * 128,
            "metadata": {"source": "test.txt"},
        }
    ]

    with subtests.test("create vector store for deletion test"):
        response = await api_client.post(
            "vector_stores", json={"name": "test-deletion-store", "dimension": 128, "model_id": "custom_model_id"}
        )
        response.raise_for_status()
        vector_store_id = response.json()["id"]

    with subtests.test("add items to vector store"):
        response = await api_client.put(f"vector_stores/{vector_store_id}", json=items)
        response.raise_for_status()

    with subtests.test("verify vector store exists before deletion"):
        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        assert response.json()["id"] == vector_store_id

    with subtests.test("delete vector store"):
        response = await api_client.delete(f"vector_stores/{vector_store_id}")
        response.raise_for_status()

    with subtests.test("verify vector store is deleted"):
        response = await api_client.get(f"vector_stores/{vector_store_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_document_deletion(subtests, api_client, acp_client):
    """Test individual document deletion functionality"""
    initial_items = [
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "First document text.",
            "embedding": [1.0] * 127 + [1.0],
            "metadata": {"source": "doc1.txt"},
        },
        {
            "document_id": "doc_002",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Second document text.",
            "embedding": [1.0] * 127 + [2.0],
            "metadata": {"source": "doc2.txt"},
        },
        {
            "document_id": "doc_003",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Third document text.",
            "embedding": [1.0] * 127 + [3.0],
            "metadata": {"source": "doc3.txt"},
        },
    ]

    with subtests.test("create vector store"):
        response = await api_client.post(
            "vector_stores", json={"name": "test-doc-deletion", "dimension": 128, "model_id": "custom_model_id"}
        )
        response.raise_for_status()
        vector_store_id = response.json()["id"]

    with subtests.test("add initial documents"):
        response = await api_client.put(f"vector_stores/{vector_store_id}", json=initial_items)
        response.raise_for_status()

    with subtests.test("verify all documents exist via search and track usage_bytes"):
        response = await api_client.post(
            f"vector_stores/{vector_store_id}/search",
            json={"query_vector": [1.0] * 128, "limit": 10},
        )
        response.raise_for_status()
        search_results = response.json()
        assert len(search_results["items"]) == 3

        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        vector_store = response.json()
        usage_bytes_before_deletion = vector_store.get("stats", {}).get("usage_bytes", 0)
        assert usage_bytes_before_deletion > 0, "Usage bytes should be greater than 0 after adding documents"

    with subtests.test("delete specific document"):
        response = await api_client.delete(f"vector_stores/{vector_store_id}/documents/doc_002")
        response.raise_for_status()

    with subtests.test("verify document was deleted and usage_bytes decreased"):
        response = await api_client.post(
            f"vector_stores/{vector_store_id}/search",
            json={"query_vector": [1.0] * 128, "limit": 10},
        )
        response.raise_for_status()
        search_results = response.json()
        assert len(search_results["items"]) == 2
        document_ids = [item["item"]["document_id"] for item in search_results["items"]]
        assert "doc_002" not in document_ids
        assert "doc_001" in document_ids
        assert "doc_003" in document_ids

        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        vector_store = response.json()
        usage_bytes_after_deletion = vector_store.get("stats", {}).get("usage_bytes", 0)
        assert usage_bytes_after_deletion < usage_bytes_before_deletion, (
            "Usage bytes should decrease after deleting a document"
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_adding_items_to_existing_documents(subtests, api_client, acp_client):
    """Test adding new items to existing documents in vector store"""
    initial_items = [
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Initial content for document 1.",
            "embedding": [1.0] * 127 + [1.0],
            "metadata": {"source": "doc1.txt", "chapter": "1"},
        },
        {
            "document_id": "doc_002",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Initial content for document 2.",
            "embedding": [1.0] * 127 + [2.0],
            "metadata": {"source": "doc2.txt", "chapter": "1"},
        },
    ]

    additional_items = [
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Additional content for document 1.",
            "embedding": [1.0] * 127 + [1.5],
            "metadata": {"source": "doc1.txt", "chapter": "2"},
        },
        {
            "document_id": "doc_003",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "New document 3 content.",
            "embedding": [1.0] * 127 + [3.0],
            "metadata": {"source": "doc3.txt", "chapter": "1"},
        },
    ]

    with subtests.test("create vector store"):
        response = await api_client.post(
            "vector_stores", json={"name": "test-add-items", "dimension": 128, "model_id": "custom_model_id"}
        )
        response.raise_for_status()
        vector_store_id = response.json()["id"]

    with subtests.test("verify initial vector store usage_bytes is 0"):
        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        vector_store = response.json()
        initial_usage_bytes = vector_store.get("stats", {}).get("usage_bytes", 0)
        assert initial_usage_bytes == 0

    with subtests.test("add initial items"):
        response = await api_client.put(f"vector_stores/{vector_store_id}", json=initial_items)
        response.raise_for_status()

    with subtests.test("verify initial items count and usage_bytes updated"):
        response = await api_client.post(
            f"vector_stores/{vector_store_id}/search",
            json={"query_vector": [1.0] * 128, "limit": 10},
        )
        response.raise_for_status()
        search_results = response.json()
        assert len(search_results["items"]) == 2

        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        vector_store = response.json()
        usage_bytes_after_initial = vector_store.get("stats", {}).get("usage_bytes", 0)
        assert usage_bytes_after_initial > 0, "Usage bytes should be greater than 0 after adding items"

    with subtests.test("add additional items to existing and new documents"):
        response = await api_client.put(f"vector_stores/{vector_store_id}", json=additional_items)
        response.raise_for_status()

    with subtests.test("verify all items are present and usage_bytes increased"):
        response = await api_client.post(
            f"vector_stores/{vector_store_id}/search",
            json={"query_vector": [1.0] * 128, "limit": 10},
        )
        response.raise_for_status()
        search_results = response.json()
        assert len(search_results["items"]) == 4

        response = await api_client.get(f"vector_stores/{vector_store_id}")
        response.raise_for_status()
        vector_store = response.json()
        usage_bytes_after_additional = vector_store.get("stats", {}).get("usage_bytes", 0)
        assert usage_bytes_after_additional > usage_bytes_after_initial, (
            "Usage bytes should increase after adding more items"
        )

    with subtests.test("verify document 1 has multiple items"):
        doc_001_items = [item for item in search_results["items"] if item["item"]["document_id"] == "doc_001"]
        assert len(doc_001_items) == 2
        chapters = {item["item"]["metadata"]["chapter"] for item in doc_001_items}
        assert chapters == {"1", "2"}

    with subtests.test("verify new document was created"):
        doc_003_items = [item for item in search_results["items"] if item["item"]["document_id"] == "doc_003"]
        assert len(doc_003_items) == 1
        assert doc_003_items[0]["item"]["text"] == "New document 3 content."


@pytest.mark.asyncio
@pytest.mark.usefixtures("clean_up")
async def test_document_listing(subtests, api_client, acp_client):
    """Test listing documents in a vector store"""
    items = [
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Content for document 1.",
            "embedding": [1.0] * 128,
            "metadata": {"source": "doc1.txt"},
        },
        {
            "document_id": "doc_001",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "More content for document 1.",
            "embedding": [2.0] * 128,
            "metadata": {"source": "doc1.txt"},
        },
        {
            "document_id": "doc_002",
            "document_type": "external",
            "model_id": "custom_model_id",
            "text": "Content for document 2.",
            "embedding": [3.0] * 128,
            "metadata": {"source": "doc2.txt"},
        },
    ]

    with subtests.test("create vector store"):
        response = await api_client.post(
            "vector_stores", json={"name": "test-doc-listing", "dimension": 128, "model_id": "custom_model_id"}
        )
        response.raise_for_status()
        vector_store_id = response.json()["id"]

    with subtests.test("add items to vector store"):
        response = await api_client.put(f"vector_stores/{vector_store_id}", json=items)
        response.raise_for_status()

    with subtests.test("list documents in vector store"):
        response = await api_client.get(f"vector_stores/{vector_store_id}/documents")
        response.raise_for_status()
        documents = response.json()["items"]

        # Should have 2 unique documents (doc_001 and doc_002)
        document_ids = {doc["id"] for doc in documents}
        assert len(document_ids) == 2
        assert "doc_001" in document_ids
        assert "doc_002" in document_ids
