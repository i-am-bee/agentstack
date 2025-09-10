# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import uuid

import pytest
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
        assert response.first_id is not None
        assert response.last_id is not None

    with subtests.test("test cursor-based pagination"):
        # Get first page with limit 2
        first_page = await Context.list(limit=2, order_by="created_at")
        assert len(first_page.items) == 2
        assert first_page.has_more is True

        # Get second page using last_id as cursor
        second_page = await Context.list(limit=2, after=first_page.last_id, order_by="created_at")
        assert len(second_page.items) == 2
        assert second_page.has_more is True

        # Get third page
        third_page = await Context.list(limit=2, after=second_page.last_id, order_by="created_at")
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
        response = await Context.list(after=nonexistent_id)
        assert len(response.items) == 5  # Should return all contexts
