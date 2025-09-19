# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

import httpx
import pytest
from kink import di
from kink.errors import ServiceError

from beeai_server.configuration import Configuration
from beeai_server.utils.github import GithubUrl

pytestmark = pytest.mark.integration


@pytest.fixture
def configuration():
    from contextlib import suppress

    orig_conf = None
    with suppress(ServiceError):
        orig_conf = di[Configuration]
    di[Configuration] = Configuration()
    yield di[Configuration]
    if orig_conf:
        di[Configuration] = orig_conf


@pytest.mark.skipif(
    condition=os.getenv("GITHUB_REGISTRY__GITHUB.IBM.COM__TOKEN", None) is None,
    reason="Skip if PAT token not provided",
)
async def test_github_private_resolve(configuration: Configuration):
    assert configuration.github_registry.get("github.ibm.com")
    resolved_url = await GithubUrl("https://github.ibm.com/Incubation/bee-api").resolve_version()
    assert resolved_url.version == "main"
    assert resolved_url.commit_hash
    async with httpx.AsyncClient() as client:
        response = await client.get(str(await resolved_url.get_raw_url("README.md")))
        assert response.text


async def test_github_public_resolve(configuration: Configuration):
    resolved_url = await GithubUrl("https://github.com/i-am-bee/beeai-platform").resolve_version()
    assert resolved_url.version == "main"
    assert resolved_url.commit_hash
    async with httpx.AsyncClient() as client:
        response = await client.get(str(await resolved_url.get_raw_url("README.md")))
        assert response.text
