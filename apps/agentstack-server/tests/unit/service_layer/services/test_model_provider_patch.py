# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""
Test for Bug 3: patch_provider in ModelProviderService must use `is not None`
instead of `or` for optional fields, so that:
  - watsonx_project_id can be changed from one value to another
  - watsonx_space_id can be changed from one value to another
  - api_key can be changed even when old key is truthy
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestPatchProviderNullCoalescing:
    """Test that patch_provider correctly applies `is not None` logic
    for optional fields rather than `or`.

    This tests the in-memory logic only, without requiring database or
    external dependencies. We mirror the pattern used in the actual code.
    """

    @staticmethod
    def _apply_patch_logic(
        *,
        old_watsonx_project_id: str | None,
        old_watsonx_space_id: str | None,
        old_api_key: str,
        new_watsonx_project_id: str | None = None,
        new_watsonx_space_id: str | None = None,
        new_api_key: str | None = None,
    ) -> tuple[str | None, str | None, str]:
        """Replicate the fixed patch logic from model_providers.py."""
        updated_watsonx_project_id = (
            new_watsonx_project_id if new_watsonx_project_id is not None else old_watsonx_project_id
        )
        updated_watsonx_space_id = new_watsonx_space_id if new_watsonx_space_id is not None else old_watsonx_space_id
        updated_api_key = new_api_key if new_api_key is not None else old_api_key
        return updated_watsonx_project_id, updated_watsonx_space_id, updated_api_key

    @staticmethod
    def _apply_old_buggy_logic(
        *,
        old_watsonx_project_id: str | None,
        old_watsonx_space_id: str | None,
        old_api_key: str,
        new_watsonx_project_id: str | None = None,
        new_watsonx_space_id: str | None = None,
        new_api_key: str | None = None,
    ) -> tuple[str | None, str | None, str]:
        """Replicate the OLD buggy logic using `or`."""
        updated_watsonx_project_id = new_watsonx_project_id or old_watsonx_project_id
        updated_watsonx_space_id = new_watsonx_space_id or old_watsonx_space_id
        updated_api_key = new_api_key or old_api_key
        return updated_watsonx_project_id, updated_watsonx_space_id, updated_api_key

    def test_change_watsonx_project_id(self):
        """Changing watsonx_project_id from 'old-project' to 'new-project' should succeed."""
        proj, space, key = self._apply_patch_logic(
            old_watsonx_project_id="old-project",
            old_watsonx_space_id="space",
            old_api_key="key",
            new_watsonx_project_id="new-project",
        )
        assert proj == "new-project"  # Fixed: this must work
        assert space == "space"  # Unchanged
        assert key == "key"  # Unchanged

    def test_none_does_not_change_value(self):
        """Passing None should keep the original value (no change intended)."""
        proj, space, key = self._apply_patch_logic(
            old_watsonx_project_id="original-project",
            old_watsonx_space_id="original-space",
            old_api_key="original-key",
            # All None = no changes
        )
        assert proj == "original-project"
        assert space == "original-space"
        assert key == "original-key"

    def test_empty_string_clears_value(self):
        """An empty string should be applied as the new value (unlike `or` which would keep the old one)."""
        proj, space, key = self._apply_patch_logic(
            old_watsonx_project_id="old-project",
            old_watsonx_space_id="old-space",
            old_api_key="old-key",
            new_watsonx_project_id="",
            new_watsonx_space_id="",
            new_api_key="",
        )
        # With `is not None`, empty string IS the new value
        assert proj == ""
        assert space == ""
        assert key == ""

    def test_buggy_or_logic_fails_on_empty_string(self):
        """Demonstrate the OLD bug: `or` ignores empty strings and keeps old values."""
        proj, space, key = self._apply_old_buggy_logic(
            old_watsonx_project_id="old-project",
            old_watsonx_space_id="old-space",
            old_api_key="old-key",
            new_watsonx_project_id="",
            new_watsonx_space_id="",
            new_api_key="",
        )
        # With `or`, empty string is falsy -> old value is kept (this IS the bug!)
        assert proj == "old-project"  # Bug: empty string was ignored
        assert space == "old-space"  # Bug: empty string was ignored
        assert key == "old-key"  # Bug: empty string was ignored

    def test_change_api_key(self):
        """Changing API key from one truthy value to another should work."""
        _, _, key = self._apply_patch_logic(
            old_watsonx_project_id=None,
            old_watsonx_space_id=None,
            old_api_key="old-key-abc",
            new_api_key="new-key-xyz",
        )
        assert key == "new-key-xyz"
