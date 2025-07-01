# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest

from beeai_server.configuration import Configuration
from beeai_server.utils.docker import DockerImageID, get_registry_image_config_and_labels

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "image",
    [
        DockerImageID(root="ghcr.io/i-am-bee/beeai-platform/official/beeai-framework/chat:agents-v0.2.14"),
        DockerImageID(root="redis:latest"),
        DockerImageID(root="icr.io/ibm-messaging/mq:latest"),
        DockerImageID(root="registry.goharbor.io/nightly/goharbor/harbor-log:v1.10.0"),
    ],
)
async def test_get_registry_image_config_and_labels(image):
    config, labels = await get_registry_image_config_and_labels(image, configuration=Configuration())
    assert config
