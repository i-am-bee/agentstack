# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from agentstack_server.api.dependencies import RequiresContextPermissions, RequiresPermissions
from agentstack_server.domain.models.permissions import AuthorizedUser, Permissions
from agentstack_server.domain.models.user import User

pytestmark = pytest.mark.unit


def create_authorized_user(
    global_permissions: Permissions,
    context_permissions: Permissions | None = None,
    token_context_id: UUID | None = None,
) -> AuthorizedUser:
    return AuthorizedUser(
        user=User(id=uuid4(), email="test@example.com"),
        global_permissions=global_permissions,
        context_permissions=context_permissions or Permissions(),
        context_id=None,  # This gets set by the dependency
        token_context_id=token_context_id,
    )


class TestRequiresPermissions:
    def test_allows_user_with_sufficient_global_permissions(self):
        dependency = RequiresPermissions(files={"read"})
        user = create_authorized_user(global_permissions=Permissions(files={"read", "write"}))
        assert dependency(user) == user

    def test_allows_user_with_exact_global_permissions(self):
        dependency = RequiresPermissions(files={"read"}, providers={"write"})
        user = create_authorized_user(global_permissions=Permissions(files={"read"}, providers={"write"}))
        assert dependency(user) == user

    def test_allows_user_with_wildcard_permissions(self):
        dependency = RequiresPermissions(files={"read"})
        user = create_authorized_user(global_permissions=Permissions(files={"*"}))
        assert dependency(user) == user

    def test_allows_admin_with_all_permissions(self):
        dependency = RequiresPermissions(files={"read"}, vector_stores={"write"})
        user = create_authorized_user(global_permissions=Permissions.all())
        assert dependency(user) == user

    def test_denies_user_with_insufficient_global_permissions(self):
        dependency = RequiresPermissions(files={"write"})
        user = create_authorized_user(global_permissions=Permissions(files={"read"}))

        with pytest.raises(HTTPException) as exc_info:
            dependency(user)
        assert exc_info.value.status_code == 403


class TestRequiresContextPermissions:
    # GLOBAL MODE TESTS (no context_id parameter)

    def test_global_mode_allows_user_with_sufficient_global_permissions(self):
        dependency = RequiresContextPermissions(files={"read"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read", "write"}),
            context_permissions=Permissions(),  # Empty context permissions
        )
        assert dependency(user, context_id=None) == user

    def test_global_mode_denies_user_with_insufficient_global_permissions(self):
        dependency = RequiresContextPermissions(files={"write"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Insufficient
            context_permissions=Permissions(files={"write"}),  # Sufficient but should be ignored
        )

        with pytest.raises(HTTPException) as exc_info:
            dependency(user, context_id=None)
        assert exc_info.value.status_code == 403

    def test_global_mode_ignores_context_permissions(self):
        """In global mode, context permissions should be completely ignored"""
        dependency = RequiresContextPermissions(files={"write"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Insufficient global
            context_permissions=Permissions(files={"write"}),  # Sufficient context (ignored)
        )

        with pytest.raises(HTTPException) as exc_info:
            dependency(user, context_id=None)
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    # CONTEXT MODE TESTS (with context_id parameter)

    def test_context_mode_allows_user_with_sufficient_global_permissions(self):
        dependency = RequiresContextPermissions(files={"read"})
        context_id = uuid4()
        user = create_authorized_user(global_permissions=Permissions(files={"read"}), context_permissions=Permissions())

        result = dependency(user, context_id=context_id)
        assert result == user
        assert result.context_id == context_id  # Should be set

    def test_context_mode_allows_user_with_sufficient_context_permissions(self):
        dependency = RequiresContextPermissions(files={"read"})
        context_id = uuid4()
        user = create_authorized_user(
            global_permissions=Permissions(),  # Empty global
            context_permissions=Permissions(files={"read"}),
        )

        result = dependency(user, context_id=context_id)
        assert result == user
        assert result.context_id == context_id

    def test_context_mode_allows_user_with_union_of_global_and_context_permissions(self):
        """Test that global + context permissions are combined"""
        dependency = RequiresContextPermissions(files={"read"}, providers={"write"})
        context_id = uuid4()
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Has files
            context_permissions=Permissions(providers={"write"}),  # Has providers
        )

        result = dependency(user, context_id=context_id)
        assert result == user
        assert result.context_id == context_id

    def test_context_mode_denies_user_with_insufficient_combined_permissions(self):
        dependency = RequiresContextPermissions(files={"write"}, providers={"read"})
        context_id = uuid4()
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Has files but wrong permission
            context_permissions=Permissions(providers={"read"}),  # Has providers
        )

        with pytest.raises(HTTPException) as exc_info:
            dependency(user, context_id=context_id)
        assert exc_info.value.status_code == 403

    # CONTEXT TOKEN VALIDATION TESTS

    def test_context_token_validation_matching_context_ids(self):
        """When token context_id matches query context_id, should work"""
        dependency = RequiresContextPermissions(files={"read"})
        context_id = uuid4()
        user = create_authorized_user(
            global_permissions=Permissions(),
            context_permissions=Permissions(files={"read"}),
            token_context_id=context_id,  # Token has this context_id
        )

        # Query param matches token context_id - should work
        result = dependency(user, context_id=context_id)
        assert result == user
        assert result.context_id == context_id

    def test_context_mode_rejects_mismatched_token_context_id(self):
        """User with context token should be rejected when context_id doesn't match"""
        dependency = RequiresContextPermissions(files={"read"})
        token_context_id = uuid4()
        request_context_id = uuid4()
        user = create_authorized_user(
            global_permissions=Permissions(),
            context_permissions=Permissions(files={"read"}),
            token_context_id=token_context_id,
        )

        with pytest.raises(HTTPException) as exc_info:
            dependency(user, context_id=request_context_id)
        assert exc_info.value.status_code == 403
        assert "Token context id does not match" in exc_info.value.detail

    def test_context_mode_sets_context_id_for_non_context_token_user(self):
        """User without context token should get context_id set when using context mode"""
        dependency = RequiresContextPermissions(files={"read"})
        context_id = uuid4()
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),
            context_permissions=Permissions(),
            token_context_id=None,  # No context token
        )

        result = dependency(user, context_id=context_id)
        assert result == user
        assert result.context_id == context_id  # Should be set by dependency

    def test_global_access_from_context_token_with_sufficient_global_perms(self):
        """CRITICAL: User with context token making global request (context_id=None) uses only global perms"""
        dependency = RequiresContextPermissions(files={"read"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Sufficient global
            context_permissions=Permissions(files={"write"}),  # Different context perms
            token_context_id=uuid4(),  # User has context token
        )

        # Global request (no context_id query param) should use only global permissions
        result = dependency(user, context_id=None)
        assert result == user
        assert result.context_id is None  # Should be None for global requests

    def test_global_access_from_context_token_denied_insufficient_global_perms(self):
        """CRITICAL: User with context token making global request denied if insufficient global perms"""
        dependency = RequiresContextPermissions(files={"write"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Insufficient global
            context_permissions=Permissions(files={"write"}),  # Sufficient context (ignored in global mode)
            token_context_id=uuid4(),  # User has context token
        )

        # Global request should fail despite having sufficient context permissions
        with pytest.raises(HTTPException) as exc_info:
            dependency(user, context_id=None)
        assert exc_info.value.status_code == 403

    # ADMIN/WILDCARD PERMISSIONS TESTS

    def test_context_mode_allows_admin_with_all_permissions(self):
        dependency = RequiresContextPermissions(files={"write"}, providers={"read"})
        context_id = uuid4()
        user = create_authorized_user(global_permissions=Permissions.all(), context_permissions=Permissions())

        result = dependency(user, context_id=context_id)
        assert result == user

    def test_context_mode_allows_wildcard_permissions(self):
        dependency = RequiresContextPermissions(files={"write"})
        context_id = uuid4()
        user = create_authorized_user(global_permissions=Permissions(), context_permissions=Permissions(files={"*"}))

        result = dependency(user, context_id=context_id)
        assert result == user

    # EDGE CASES

    def test_empty_required_permissions_always_allowed(self):
        dependency = RequiresContextPermissions()  # No permissions required
        context_id = uuid4()
        user = create_authorized_user(global_permissions=Permissions(), context_permissions=Permissions())
        assert dependency(user, context_id=context_id) == user

    def test_context_mode_with_no_permissions_at_all(self):
        dependency = RequiresContextPermissions(files={"read"})
        context_id = uuid4()
        user = create_authorized_user(global_permissions=Permissions(), context_permissions=Permissions())

        with pytest.raises(HTTPException) as exc_info:
            dependency(user, context_id=context_id)
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    def test_denies_user_with_different_permission_type(self):
        dependency = RequiresPermissions(files={"read"})
        user = create_authorized_user(global_permissions=Permissions(providers={"read"}))

        with pytest.raises(HTTPException) as exc_info:
            dependency(user)
        assert exc_info.value.status_code == 403

    def test_ignores_context_permissions(self):
        """RequiresPermissions should ONLY check global permissions, ignoring context permissions"""
        dependency = RequiresPermissions(files={"write"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"}),  # Insufficient global
            context_permissions=Permissions(files={"write"}),  # Sufficient context (should be ignored)
            token_context_id=uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            dependency(user)
        assert exc_info.value.status_code == 403

    def test_multiple_permission_types(self):
        dependency = RequiresPermissions(files={"read"}, vector_stores={"write"}, providers={"read"})
        user = create_authorized_user(
            global_permissions=Permissions(
                files={"read", "write"}, vector_stores={"write"}, providers={"read", "write"}
            )
        )
        assert dependency(user) == user

    def test_fails_on_partial_permission_match(self):
        dependency = RequiresPermissions(files={"read"}, vector_stores={"write"})
        user = create_authorized_user(
            global_permissions=Permissions(files={"read"})  # Missing vector_stores
        )

        with pytest.raises(HTTPException) as exc_info:
            dependency(user)
        assert exc_info.value.status_code == 403
