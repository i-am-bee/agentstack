import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import base64
import json
import sys
import os

# Ensure src is in path for imports to work if not installed in editable mode
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from agentstack_cli.commands.build import client_side_build

async def _test_client_side_build_skip_extraction():
    with patch('agentstack_cli.commands.build.run_command') as mock_run_command, \
         patch('agentstack_cli.commands.build.open_process') as mock_open_process, \
         patch('agentstack_cli.commands.build.find_free_port', return_value=8000), \
         patch('agentstack_cli.commands.build.capture_output') as mock_capture_output, \
         patch('agentstack_cli.commands.build.AsyncRetrying') as mock_async_retrying:

        # Mock capture_output context manager
        mock_capture = MagicMock()
        mock_capture.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_capture.__aexit__ = AsyncMock()
        mock_capture_output.return_value = mock_capture

        # Mock process context manager
        mock_process = MagicMock()
        mock_process.__aenter__ = AsyncMock(return_value=mock_process)
        mock_process.__aexit__ = AsyncMock()
        mock_open_process.return_value = mock_process

        # Mock AsyncRetrying
        mock_retry = MagicMock()
        mock_retry.__aiter__.return_value = [MagicMock()]
        mock_async_retrying.return_value = mock_retry

        # Mock run_command to avoid issues and capture calls
        mock_run_command.return_value = MagicMock(returncode=0)

        await client_side_build(
            context=".",
            import_image=False,
            skip_agent_card_extraction=True,
            verbose=True
        )

        # Verify open_process was NOT called
        assert not mock_open_process.called, "Container should NOT have been launched"

        calls = mock_run_command.call_args_list
        found_label = False
        for call in calls:
            args, kwargs = call
            command = None
            if args:
                command = args[0]
            elif 'command' in kwargs:
                command = kwargs['command']

            if command:
                for arg in command:
                    if arg.startswith("--label=beeai.dev.agent.json="):
                        parts = arg.split("=", 2)
                        if len(parts) >= 3:
                            val_b64 = parts[2]
                            val_json = base64.b64decode(val_b64).decode()
                            if val_json == "null":
                                found_label = True

        assert found_label, "Expected label with 'null' value not found"

def test_client_side_build_skip_extraction():
    asyncio.run(_test_client_side_build_skip_extraction())

async def _test_client_side_build_default():
    with patch('agentstack_cli.commands.build.run_command') as mock_run_command, \
         patch('agentstack_cli.commands.build.open_process') as mock_open_process, \
         patch('agentstack_cli.commands.build.find_free_port', return_value=8000), \
         patch('agentstack_cli.commands.build.capture_output') as mock_capture_output, \
         patch('agentstack_cli.commands.build.AsyncRetrying') as mock_async_retrying, \
         patch('agentstack_cli.commands.build.AsyncClient') as mock_async_client:

        # Mock capture_output context manager
        mock_capture = MagicMock()
        mock_capture.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_capture.__aexit__ = AsyncMock()
        mock_capture_output.return_value = mock_capture

        # Mock process context manager
        mock_process = MagicMock()
        mock_process.__aenter__ = AsyncMock(return_value=mock_process)
        mock_process.__aexit__ = AsyncMock()
        mock_open_process.return_value = mock_process

        # Mock AsyncRetrying
        mock_retry = MagicMock()
        mock_retry.__aiter__.return_value = [MagicMock()]
        mock_async_retrying.return_value = mock_retry

        # Mock run_command to avoid issues and capture calls
        mock_run_command.return_value = MagicMock(returncode=0)

        # Mock AsyncClient
        mock_client_instance = MagicMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Make .get() return an awaitable
        resp_mock = MagicMock()
        resp_mock.status_code = 200
        resp_mock.raise_for_status = MagicMock()
        resp_mock.json.return_value = {"test": "card"}

        async def async_get(*args, **kwargs):
             return resp_mock

        mock_client_instance.get.side_effect = async_get

        # Call without skip flag (default False)
        await client_side_build(
            context=".",
            import_image=False,
            verbose=True
        )

        # Verify open_process was called
        assert mock_open_process.called, "Container should have been launched"

        # Verify run_command was called with the correct label
        calls = mock_run_command.call_args_list
        found_label = False
        for call in calls:
            args, kwargs = call
            command = None
            if args:
                command = args[0]
            elif 'command' in kwargs:
                command = kwargs['command']

            if command:
                for arg in command:
                    if arg.startswith("--label=beeai.dev.agent.json="):
                        parts = arg.split("=", 2)
                        if len(parts) >= 3:
                            val_b64 = parts[2]
                            val_json = base64.b64decode(val_b64).decode()
                            card = json.loads(val_json)
                            if card.get("test") == "card":
                                found_label = True

        assert found_label, "Expected label with extracted card not found"

def test_client_side_build_default():
    asyncio.run(_test_client_side_build_default())
