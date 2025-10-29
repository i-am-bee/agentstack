# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest

from agentstack_server.domain.models.permissions import Permissions, ResourceIdPermission

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "user_perms, required_perms, expected",
    [
        # Empty permissions
        (Permissions(), Permissions(), True),
        # Exact match
        (
            Permissions(files={"read"}, vector_stores={"write"}),
            Permissions(files={"read"}, vector_stores={"write"}),
            True,
        ),
        # Subset permissions
        (
            Permissions(files={"read", "write"}, vector_stores={"read", "write"}),
            Permissions(files={"read"}, vector_stores={"write"}),
            True,
        ),
        # Insufficient permissions
        (Permissions(files={"read"}), Permissions(files={"write"}), False),
        # Missing permission type
        (Permissions(files={"read"}), Permissions(vector_stores={"read"}), False),
        # Wildcard permission
        (Permissions(files={"*"}), Permissions(files={"read", "write", "extract"}), True),
        # Wildcard vs specific
        (Permissions(files={"*"}), Permissions(files={"read"}), True),
        # Mixed permissions
        (
            Permissions(
                files={"read", "write"},
                vector_stores={"*"},
                feedback={"write"},
                providers={"read"},
            ),
            Permissions(
                files={"read"},
                vector_stores={"extract"},
                feedback={"write"},
                providers={"read"},
            ),
            True,
        ),
        # All permission types check
        (
            Permissions(
                files={"*"},
                feedback={"write"},
                vector_stores={"read", "write", "extract"},
                llm={"*"},
                embeddings={"*"},
                a2a_proxy={"*"},
                providers={"read", "write"},
                provider_variables={"read", "write"},
                contexts={"read", "write"},
            ),
            Permissions(
                files={"read"},
                feedback={"write"},
                vector_stores={"extract"},
                providers={"read"},
                provider_variables={"write"},
                contexts={"read"},
            ),
            True,
        ),
    ],
)
def test_check_permissions(user_perms, required_perms, expected):
    assert user_perms.check(required_perms) is expected


def test_check_resource_id_wildcard():
    # Test that wildcard works for resource-type permissions
    user_perms = Permissions(llm={"*"})
    required_perms = Permissions(llm={"*"})
    assert user_perms.check(required_perms) is True


def test_check_resource_id_permissions():
    resource1 = ResourceIdPermission(id="llm-1")
    resource2 = ResourceIdPermission(id="llm-2")

    user_perms = Permissions(llm={resource1})
    required_perms = Permissions(llm={resource1})
    assert user_perms.check(required_perms) is True

    required_perms_different = Permissions(llm={resource2})
    assert user_perms.check(required_perms_different) is False


def test_admin_all_permissions_check():
    admin_perms = Permissions.all()

    required_perms = Permissions(
        files={"read", "write", "extract"},
        vector_stores={"read", "write", "extract"},
        feedback={"write"},
        providers={"read", "write"},
        provider_variables={"read", "write"},
        contexts={"read", "write"},
        a2a_proxy={"*"},
    )

    assert admin_perms.check(required_perms) is True
    assert admin_perms.allow_all is True


def test_admin_all_permissions_empty_required():
    admin_perms = Permissions.all()
    required_perms = Permissions()
    assert admin_perms.check(required_perms) is True


@pytest.mark.parametrize(
    "perms1, perms2, expected",
    [
        # Basic union - files and vector_stores
        (
            Permissions(files={"read"}, vector_stores={"write"}),
            Permissions(files={"write"}, providers={"read"}),
            {"files": {"read", "write"}, "vector_stores": {"write"}, "providers": {"read"}},
        ),
        # Empty permissions
        (Permissions(), Permissions(files={"read"}), {"files": {"read"}}),
        # Wildcard union
        (Permissions(files={"read", "write"}), Permissions(files={"*"}), {"files": {"*"}}),
        # LLM permissions union
        (Permissions(llm={"*"}), Permissions(llm={"*"}, embeddings={"*"}), {"llm": {"*"}, "embeddings": {"*"}}),
        # Multiple permission types
        (
            Permissions(files={"read"}, provider_variables={"read"}, contexts={"write"}),
            Permissions(files={"write"}, provider_variables={"write"}, providers={"read"}),
            {
                "files": {"read", "write"},
                "providers": {"read"},
                "provider_variables": {"read", "write"},
                "contexts": {"write"},
            },
        ),
        # A2A proxy and feedback
        (
            Permissions(a2a_proxy={"*"}, feedback={"write"}),
            Permissions(feedback={"write"}),
            {"feedback": {"write"}, "a2a_proxy": {"*"}},
        ),
    ],
)
def test_union_comprehensive_cases(perms1, perms2, expected):
    result = perms1.union(perms2)
    assert result == perms1 | perms2

    result = {k: set(v) for k, v in result.model_dump(serialize_as_any=True).items() if v}
    assert result == expected


def test_union_admin_permissions():
    admin_perms = Permissions.all()
    regular_perms = Permissions(files={"read"})
    assert admin_perms.union(regular_perms).allow_all is True
    assert regular_perms.union(admin_perms).allow_all is True


def test_union_resource_id_permissions():
    resource1 = ResourceIdPermission(id="llm-1")
    resource2 = ResourceIdPermission(id="llm-2")

    perms1 = Permissions(llm={resource1})
    perms2 = Permissions(llm={resource2})

    result = perms1.union(perms2)

    assert len(result.llm) == 2
    assert resource1 in result.llm
    assert resource2 in result.llm


def test_permissions_basic_functionality():
    perms = Permissions(files={"read"})
    assert isinstance(perms.files, frozenset)
    assert "read" in perms.files
