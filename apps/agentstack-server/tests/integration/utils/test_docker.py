# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from kink import di
from kink.errors import ServiceError

from agentstack_server.configuration import Configuration
from agentstack_server.utils.docker import DockerImageID

pytestmark = pytest.mark.integration


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
    "image",
    [
        "ghcr.io/i-am-bee/agentstack/agents/chat:0.4.0-rc1",
        "redis:latest",
        "icr.io/ibm-messaging/mq:latest",
        "registry.goharbor.io/nightly/goharbor/harbor-log:v1.10.0",
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_get_image_labels(image, configuration):
    resolved_image = await DockerImageID(root=image).resolve_version()
    assert resolved_image.digest
    await resolved_image.get_labels()
