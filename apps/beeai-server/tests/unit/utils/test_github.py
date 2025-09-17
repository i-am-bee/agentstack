# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from pytest_httpx import HTTPXMock

from beeai_server.utils.github import GithubUrl
from beeai_server.utils.utils import filter_dict

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://github.com/myorg/myrepo", {"org": "myorg", "repo": "myrepo"}),
        ("git+https://github.com/myorg/myrepo", {"org": "myorg", "repo": "myrepo"}),
        ("git+https://github.com/myorg/myrepo.git", {"org": "myorg", "repo": "myrepo"}),
        ("https://github.com/myorg/myrepo.git", {"org": "myorg", "repo": "myrepo"}),
        ("https://github.com/myorg/myrepo", {"org": "myorg", "repo": "myrepo"}),
        ("https://github.com/myorg/myrepo#path=/a/b.txt", {"org": "myorg", "repo": "myrepo", "path": "a/b.txt"}),
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
def test_parses_github_url(url, expected):
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
        "git@github.com:org/repo.git",  # SSH format (not supported)
    ],
)
def test_invalid_urls(url):
    """Test that invalid URLs raise ValueError."""
    with pytest.raises(ValueError):
        GithubUrl(url)


@pytest.mark.skip("TODO: fix this test")
async def test_resolve_version(httpx_mock: HTTPXMock):
    url = "http://github.com/my-org/my-repo"
    location = "https://github.com/my-org/my-repo/blob/main/dummy"
    httpx_mock.add_response(status_code=304, headers={"location": location})

    url = GithubUrl(url)
    assert url.version is None

    await url.resolve_version()

    assert url.version == "main"

    request = httpx_mock.get_request()
    assert str(request.url).startswith("https://github.com/my-org/my-repo/blob/-/")
