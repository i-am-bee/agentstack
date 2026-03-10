# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the FileSystem extension."""

from unittest.mock import MagicMock, patch

import pytest

from agentstack_sdk.a2a.extensions.services.filesystem import (
    AgentStackFileSystem,
    FileSystemExtensionServer,
    FileSystemExtensionSpec,
)
from agentstack_sdk.a2a.extensions.services.platform import (
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)

pytestmark = pytest.mark.unit


class TestFileSystemExtensionSpec:
    """Tests for FileSystemExtensionSpec."""

    def test_uri_is_set(self):
        assert FileSystemExtensionSpec.URI == "https://a2a-extensions.agentstack.beeai.dev/services/filesystem/v1"

    def test_spec_creation(self):
        spec = FileSystemExtensionSpec()
        assert spec is not None

    def test_description_is_set(self):
        assert FileSystemExtensionSpec.DESCRIPTION is not None
        assert "fsspec" in FileSystemExtensionSpec.DESCRIPTION.lower()


class TestAgentStackFileSystem:
    """Tests for AgentStackFileSystem."""

    def test_protocol_is_set(self):
        assert AgentStackFileSystem.protocol == "agentstack"

    def test_normalize_path_with_prefix(self):
        platform_mock = MagicMock(spec=PlatformApiExtensionServer)
        fs = AgentStackFileSystem(platform=platform_mock, prefix="/data")
        assert fs._normalize_path("myfile.csv") == "/data/myfile.csv"
        assert fs._normalize_path("/myfile.csv") == "/data/myfile.csv"

    def test_normalize_path_without_prefix(self):
        platform_mock = MagicMock(spec=PlatformApiExtensionServer)
        fs = AgentStackFileSystem(platform=platform_mock)
        assert fs._normalize_path("myfile.csv") == "myfile.csv"
        assert fs._normalize_path("/myfile.csv") == "myfile.csv"

    def test_strip_prefix(self):
        platform_mock = MagicMock(spec=PlatformApiExtensionServer)
        fs = AgentStackFileSystem(platform=platform_mock, prefix="/data")
        assert fs._strip_prefix("/data/myfile.csv") == "myfile.csv"
        assert fs._strip_prefix("otherfile.csv") == "otherfile.csv"


class TestFileSystemExtensionServer:
    """Tests for FileSystemExtensionServer."""

    def test_server_initialization(self):
        """Test server can be created using model_construct (bypasses validation)."""
        platform_mock = MagicMock(spec=PlatformApiExtensionServer)
        server = FileSystemExtensionServer.model_construct(platform=platform_mock)
        assert server.platform == platform_mock

    def test_server_initialization_with_prefix(self):
        platform_mock = MagicMock(spec=PlatformApiExtensionServer)
        server = FileSystemExtensionServer.model_construct(platform=platform_mock, prefix="/mydata")
        assert server.prefix == "/mydata"

    def test_fs_property_creates_filesystem(self):
        platform_mock = MagicMock(spec=PlatformApiExtensionServer)
        server = FileSystemExtensionServer.model_construct(platform=platform_mock, prefix="/test")
        fs = server.fs
        assert isinstance(fs, AgentStackFileSystem)
        assert fs._prefix == "/test"
        # Should return same instance
        assert server.fs is fs
