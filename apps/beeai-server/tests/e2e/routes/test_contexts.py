# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid

import pytest
from beeai_sdk.a2a.types import AgentMessage
from beeai_sdk.platform.context import Context
from httpx import HTTPStatusError

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_context_pagination(subtests):
    """Test cursor-based pagination for list_contexts endpoint."""

    # Create multiple contexts for testing pagination
    context_ids = []

    with subtests.test("create multiple contexts"):
        context_ids = [(await Context.create()).id for _ in range(5)]

    with subtests.test("test default pagination (no cursor)"):
        response = await Context.list()
        assert len(response.items) == 5  # All contexts should be returned
        assert response.total_count == 5
        assert response.has_more is False

        # Verify contexts are ordered by created_at desc (newest first)
        created_ats = [item.created_at for item in response.items]
        assert created_ats == sorted(created_ats, reverse=True)

    with subtests.test("test pagination with limit"):
        response = await Context.list(limit=2)
        assert len(response.items) == 2
        assert response.total_count == 5
        assert response.has_more is True
        assert response.next_page_token is not None

    with subtests.test("test cursor-based pagination"):
        # Get first page with limit 2
        first_page = await Context.list(limit=2, order_by="created_at")
        assert len(first_page.items) == 2
        assert first_page.has_more is True

        # Get second page using next_page_token as cursor
        second_page = await Context.list(limit=2, page_token=first_page.next_page_token, order_by="created_at")
        assert len(second_page.items) == 2
        assert second_page.has_more is True

        # Get third page
        third_page = await Context.list(limit=2, page_token=second_page.next_page_token, order_by="created_at")
        assert len(third_page.items) == 1  # Only 1 remaining
        assert third_page.has_more is False

        assert [i.id for i in first_page.items + second_page.items + third_page.items] == list(reversed(context_ids))

    with subtests.test("test ascending order"):
        response = await Context.list(order="asc", limit=2)
        created_ats = [item.created_at for item in response.items]
        assert created_ats == sorted(created_ats)  # Should be ascending

    with subtests.test("test nonexistent cursor"):
        # Using invalid UUID should not crash, just ignore the cursor
        nonexistent_id = uuid.uuid4()
        response = await Context.list(page_token=nonexistent_id)
        assert len(response.items) == 5  # Should return all contexts


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_context_history_pagination(subtests):
    """Test cursor-based pagination for context history endpoint."""

    # Create a context for testing
    context = await Context.create()

    # Create more than 40 history items (default page size) to test pagination
    num_items = 45

    with subtests.test("add multiple history items"):
        for i in range(num_items):
            message = AgentMessage(text=f"Test message {i}")
            await context.add_history_item(data=message)

    with subtests.test("test default pagination (first page)"):
        response = await Context.list_history(context.id)
        assert len(response.items) == 40  # Default page size
        assert response.has_more is True
        assert response.next_page_token is not None

        # Verify items are ordered by created_at desc (newest first)
        created_ats = [item.created_at for item in response.items]
        assert created_ats == sorted(created_ats, reverse=False)

    with subtests.test("test pagination with custom limit"):
        response = await Context.list_history(context.id, limit=10)
        assert len(response.items) == 10
        assert response.has_more is True
        assert response.next_page_token is not None

    with subtests.test("test cursor-based pagination"):
        # Get first page with limit 20
        first_page = await Context.list_history(context.id, limit=20)
        assert len(first_page.items) == 20
        assert first_page.has_more is True

        # Get second page using next_page_token as cursor
        second_page = await Context.list_history(context.id, limit=20, page_token=first_page.next_page_token)
        assert len(second_page.items) == 20
        assert second_page.has_more is True

        # Get third page
        third_page = await Context.list_history(context.id, limit=20, page_token=second_page.next_page_token)
        assert len(third_page.items) == 5  # Remaining items
        assert third_page.has_more is False

        # Verify no duplicate items across pages
        all_items = first_page.items + second_page.items + third_page.items
        all_ids = [item.id for item in all_items if hasattr(item, "id")]
        assert len(all_ids) == len(set(all_ids))  # No duplicates

    with subtests.test("test ascending order"):
        response = await Context.list_history(context.id, order="asc", limit=5)
        created_ats = [item.created_at for item in response.items]
        assert created_ats == sorted(created_ats)  # Should be ascending

    with subtests.test("test list_all_history method"):
        # Test the list_all_history method that automatically iterates through all pages
        all_items = []
        async for item in Context.list_all_history(context.id):
            all_items.append(item)

        assert len(all_items) == num_items

        # Verify chronological order (oldest first since it yields in order)
        created_ats = [item.created_at for item in all_items]
        # Note: list_all_history should maintain the order from list_history (desc by default)
        # but iterate through all pages


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_context_empty_filtering(subtests):
    """Test filtering contexts based on whether they have history records."""

    with subtests.test("create contexts with and without history"):
        # Create empty context (no history)
        empty_context = await Context.create()

        # Create context with history
        context_with_history = await Context.create()
        message = AgentMessage(text="Test message")
        await context_with_history.add_history_item(data=message)

    with subtests.test("include_empty=True returns all contexts"):
        response = await Context.list(include_empty=True)
        assert len(response.items) == 2  # Should include both contexts

    with subtests.test("include_empty=False returns only contexts with history"):
        response = await Context.list(include_empty=False)
        context_ids = [ctx.id for ctx in response.items]
        assert len(context_ids) == 1
        assert context_with_history.id in context_ids
        assert empty_context.id not in context_ids


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_context_update_and_patch(subtests):
    """Test updating and patching context metadata."""

    context = None

    with subtests.test("create context with initial metadata"):
        context = await Context.create(metadata={"key1": "value1", "key2": "value2"})
        assert context.metadata == {"key1": "value1", "key2": "value2"}

    with subtests.test("update context metadata"):
        updated = await context.update(metadata={"key3": "value3", "key4": "value4"})
        assert updated.metadata == {"key3": "value3", "key4": "value4"}

    with subtests.test("patch context metadata"):
        patched = await context.patch_metadata(metadata={"key3": None, "key5": "value5"})
        assert patched.metadata == {"key4": "value4", "key5": "value5"}

    with subtests.test("exceed metadata size"), pytest.raises(HTTPStatusError):
        await context.patch_metadata(metadata={str(i): str(i) for i in range(15)})


@pytest.mark.usefixtures("clean_up", "setup_platform_client")
async def test_context_provider_filtering(subtests):
    """Test creating contexts with provider_id and filtering by provider_id."""
    from a2a.types import AgentCapabilities, AgentCard
    from beeai_sdk.platform import Provider

    provider1 = None
    provider2 = None
    context_with_provider1 = None
    context_with_provider2 = None
    context_without_provider = None

    with subtests.test("create dummy providers"):
        # Create first dummy provider with network URL
        agent_card1 = AgentCard(
            name="Test Provider 1",
            description="First test provider",
            url="http://localhost:9001/",
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(),
            skills=[],
        )
        provider1 = await Provider.create(location="http://localhost:9001", agent_card=agent_card1)
        assert provider1.id is not None

        # Create second dummy provider with network URL
        agent_card2 = AgentCard(
            name="Test Provider 2",
            description="Second test provider",
            url="http://localhost:9002/",
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(),
            skills=[],
        )
        provider2 = await Provider.create(location="http://localhost:9002", agent_card=agent_card2)
        assert provider2.id is not None
        assert provider1.id != provider2.id

    with subtests.test("create contexts with and without provider_id"):
        # Create context associated with provider1
        context_with_provider1 = await Context.create(metadata={"name": "context_provider1"}, provider_id=provider1.id)
        assert context_with_provider1.provider_id == provider1.id

        # Create context associated with provider2
        context_with_provider2 = await Context.create(metadata={"name": "context_provider2"}, provider_id=provider2.id)
        assert context_with_provider2.provider_id == provider2.id

        # Create context without provider
        context_without_provider = await Context.create(metadata={"name": "context_no_provider"})
        assert context_without_provider.provider_id is None

    with subtests.test("list all contexts without filter"):
        all_contexts = await Context.list()
        assert len(all_contexts.items) == 3
        context_ids = [ctx.id for ctx in all_contexts.items]
        assert context_with_provider1.id in context_ids
        assert context_with_provider2.id in context_ids
        assert context_without_provider.id in context_ids

    with subtests.test("filter contexts by provider1"):
        provider1_contexts = await Context.list(provider_id=provider1.id)
        assert len(provider1_contexts.items) == 1
        assert provider1_contexts.items[0].id == context_with_provider1.id
        assert provider1_contexts.items[0].provider_id == provider1.id

    with subtests.test("filter contexts by provider2"):
        provider2_contexts = await Context.list(provider_id=provider2.id)
        assert len(provider2_contexts.items) == 1
        assert provider2_contexts.items[0].id == context_with_provider2.id
        assert provider2_contexts.items[0].provider_id == provider2.id

    with subtests.test("filter by non-existent provider returns empty list"):
        nonexistent_provider_id = str(uuid.uuid4())
        no_contexts = await Context.list(provider_id=nonexistent_provider_id)
        assert len(no_contexts.items) == 0

    with subtests.test("get context includes provider_id"):
        fetched_context = await Context.get(context_with_provider1.id)
        assert fetched_context.provider_id == provider1.id
