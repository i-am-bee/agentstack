# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

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
        DockerImageID(root="ghcr.io/i-am-bee/beeai-platform/official/beeai-framework/chat:agents-v0.2.14"),
        DockerImageID(root="redis:latest"),
        DockerImageID(root="icr.io/ibm-messaging/mq:latest"),
        DockerImageID(root="registry.goharbor.io/nightly/goharbor/harbor-log:v1.10.0"),
    ],
)
async def test_get_image_labels(image, configuration):
    resolved_image = await image.resolve_version()
    assert resolved_image.digest
    await resolved_image.get_labels()
