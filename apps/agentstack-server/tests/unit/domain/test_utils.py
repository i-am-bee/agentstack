# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
from pydantic import HttpUrl

from agentstack_server.domain.utils import bridge_k8s_to_localhost, bridge_localhost_to_k8s


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected_url",
    [
        ("http://localhost:8080", "http://host.docker.internal:8080/"),
        ("http://127.0.0.1:8080", "http://host.docker.internal:8080/"),
        ("http://127.0.1.1:8000", "http://host.docker.internal:8000/"),
        ("http://0.0.0.0:3000", "http://host.docker.internal:3000/"),
        ("http://example.com:8080", "http://example.com:8080/"),
        ("https://localhost", "https://host.docker.internal/"),
    ],
)
def test_bridge_localhost_to_k8s(input_url, expected_url):
    result = bridge_localhost_to_k8s(input_url)
    assert isinstance(result, HttpUrl)
    assert str(result) == expected_url


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected_url",
    [
        ("http://host.docker.internal:8080", "http://localhost:8080/"),
        ("https://host.docker.internal", "https://localhost/"),
        ("http://example.com:8080", "http://example.com:8080/"),
    ],
)
def test_bridge_k8s_to_localhost(input_url, expected_url):
    result = bridge_k8s_to_localhost(input_url)
    assert isinstance(result, HttpUrl)
    assert str(result) == expected_url
