# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import pytest

from beeai_server.utils.docker import DockerImageID
from beeai_server.utils.utils import filter_dict

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "image_id,expected",
    [
        ("ubuntu:20.04", {"repository": "library/ubuntu", "tag": "20.04"}),
        ("library/ubuntu:latest", {"repository": "library/ubuntu"}),
        ("docker.io/library/ubuntu:latest", {"repository": "library/ubuntu"}),
        (
            "registry.example.com/image:1.0",
            {"registry": "registry.example.com", "repository": "image", "tag": "1.0"},
        ),
        (
            "registry.example.com/project/image:1.0",
            {"registry": "registry.example.com", "repository": "project/image", "tag": "1.0"},
        ),
        (
            "registry.example.com/project/image",
            {"registry": "registry.example.com", "repository": "project/image"},
        ),
        ("user/repo:tag", {"repository": "user/repo", "tag": "tag"}),
        (
            "beeai-platform-registry-svc.default:5001/i-am-bee/beeai-platform-agent-starter/agent:036bb38e871dbf0d92d049b0237ae1bcac14e136",
            {
                "registry": "beeai-platform-registry-svc.default:5001",
                "repository": "i-am-bee/beeai-platform-agent-starter/agent",
                "tag": "036bb38e871dbf0d92d049b0237ae1bcac14e136",
            },
        ),
        (
            "custom.registry/team/product/component:v1.2.3",
            {"registry": "custom.registry", "repository": "team/product/component", "tag": "v1.2.3"},
        ),
    ],
)
def test_parses_docker_url(image_id, expected):
    image_id = DockerImageID(image_id)
    expected = {"registry": "docker.io", "tag": "latest", **expected}
    assert (
        filter_dict({"registry": image_id.registry, "repository": image_id.repository, "tag": image_id.tag}) == expected
    )
