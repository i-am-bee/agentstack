# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentstack_sdk.server.server import Server

pytestmark = pytest.mark.unit


def _make_server_with_agent() -> Server:
    """Create a Server instance with minimal mocks for _load_variables testing."""
    server = Server()
    server._provider_id = "test-provider-id"

    # Mock the uvicorn server
    mock_uvicorn = MagicMock()
    mock_uvicorn.config = MagicMock()
    server.server = mock_uvicorn

    # Mock a minimal agent with no extensions
    mock_agent = MagicMock()
    mock_agent.card.capabilities.extensions = []
    server._agent = mock_agent

    return server


@patch("agentstack_sdk.server.server.Provider")
async def test_load_variables_detects_value_changes(mock_provider_cls):
    """Bug 1: _load_variables dirty check must detect when env var VALUES change,
    even if the set of keys stays the same."""
    server = _make_server_with_agent()

    # First load: FOO=bar
    mock_provider_cls.list_variables = AsyncMock(return_value={"FOO": "bar"})
    await server._load_variables(first_run=True)
    assert os.environ.get("FOO") == "bar"

    # Second load: FOO=baz (value changed, key set unchanged)
    mock_provider_cls.list_variables = AsyncMock(return_value={"FOO": "baz"})
    await server._load_variables(first_run=False)

    # The new value must be in os.environ
    assert os.environ.get("FOO") == "baz"

    # The internal tracker must reflect the new value so dirty=True was detected
    assert server._all_configured_variables.get("FOO") == "baz"

    # Cleanup
    os.environ.pop("FOO", None)


@patch("agentstack_sdk.server.server.Provider")
async def test_load_variables_detects_key_removal(mock_provider_cls):
    """Existing behaviour: removed keys should be cleaned from os.environ."""
    server = _make_server_with_agent()

    mock_provider_cls.list_variables = AsyncMock(return_value={"A": "1", "B": "2"})
    await server._load_variables(first_run=True)
    assert os.environ.get("A") == "1"
    assert os.environ.get("B") == "2"

    # Remove key B
    mock_provider_cls.list_variables = AsyncMock(return_value={"A": "1"})
    await server._load_variables(first_run=False)
    assert os.environ.get("A") == "1"
    assert os.environ.get("B") is None
    assert "B" not in server._all_configured_variables

    # Cleanup
    os.environ.pop("A", None)


@patch("agentstack_sdk.server.server.Provider")
async def test_load_variables_no_change_is_not_dirty(mock_provider_cls):
    """When nothing changed, the dirty flag should be False."""
    server = _make_server_with_agent()

    mock_provider_cls.list_variables = AsyncMock(return_value={"X": "1"})
    await server._load_variables(first_run=True)

    # Same values again
    mock_provider_cls.list_variables = AsyncMock(return_value={"X": "1"})
    await server._load_variables(first_run=False)

    # Internal state unchanged
    assert server._all_configured_variables == {"X": "1"}

    # Cleanup
    os.environ.pop("X", None)
