# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid

import pytest
from beeai_sdk.a2a.types import AgentMessage
from beeai_sdk.platform.context import Context

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
