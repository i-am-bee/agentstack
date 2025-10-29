# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from kink import di
from kink.errors import ServiceError

from agentstack_server.configuration import Configuration
from agentstack_server.utils.github import GithubUrl
from agentstack_server.utils.utils import filter_dict

pytestmark = pytest.mark.unit


@pytest.fixture
def configuration():
    from contextlib import suppress

    orig_conf = None
    with suppress(ServiceError):
        orig_conf = di[Configuration]
    di[Configuration] = Configuration()
    yield
    if orig_conf:
        di[Configuration] = orig_conf


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://github.com/myorg/myrepo", {"org": "myorg", "repo": "myrepo"}),
        ("git+https://github.com/myorg/myrepo", {"org": "myorg", "repo": "myrepo"}),
        ("git+https://github.com/myorg/myrepo.git", {"org": "myorg", "repo": "myrepo"}),
        ("https://github.com/myorg/myrepo.git", {"org": "myorg", "repo": "myrepo"}),
        ("https://github.com/myorg/myrepo", {"org": "myorg", "repo": "myrepo"}),
        ("https://github.com/myorg/myrepo#path=/a/b.txt", {"org": "myorg", "repo": "myrepo", "path": "a/b.txt"}),
        ("https://github.ibm.com/myorg/myrepo#path=/a/b.txt", {"org": "myorg", "repo": "myrepo", "path": "a/b.txt"}),
        ("https://github.com/myorg/myrepo@1.0.0", {"org": "myorg", "repo": "myrepo", "version": "1.0.0"}),
        ("https://github.com/myorg/myrepo.git@1.0.0", {"org": "myorg", "repo": "myrepo", "version": "1.0.0"}),
        (
            "https://github.com/myorg/myrepo@feature/branch-name",
            {"org": "myorg", "repo": "myrepo", "version": "feature/branch-name"},
        ),
        (
            "https://github.com/myorg/myrepo.git@1.0.0#path=/a/b.txt",
            {"org": "myorg", "repo": "myrepo", "version": "1.0.0", "path": "a/b.txt"},
        ),
        ("https://github.com/org.dot/repo.dot.git", {"org": "org.dot", "repo": "repo.dot"}),
    ],
)
def test_parses_github_url(url, expected, configuration):
    url = GithubUrl(url)
    assert filter_dict({"org": url.org, "repo": url.repo, "version": url.version, "path": url.path}) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",  # Empty string
        "http://github.com",  # Missing org and repo
        "git+invalid://github.com/org/repo",  # Invalid protocol
        "https://github.com/org",  # Missing repo
        "https://gitlab.com/org/repo",  # Different domain
        "https://github.com /org/repo",  # extra space
        "https://github.com/org /repo",  # extra space
        "https://github.com/org/repo#path=;DROP TABLE",  # extra path
        "git@github.com:org/repo.git",  # SSH format (not supported)
    ],
)
def test_invalid_urls(url):
    """Test that invalid URLs raise ValueError."""
    with pytest.raises(ValueError):
        GithubUrl(url)
