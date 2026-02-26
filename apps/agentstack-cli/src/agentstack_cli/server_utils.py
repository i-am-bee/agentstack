# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys

from InquirerPy import inquirer

from agentstack_cli.configuration import Configuration
from agentstack_cli.console import console


def require_active_server() -> str:
    """Return the active server URL or exit if none is selected."""
    if url := Configuration().auth_manager.active_server:
        return url
    console.error("No server selected.")
    console.hint(
        "Run [green]agentstack platform start[/green] to start a local server, or [green]agentstack server login[/green] to connect to a remote one."
    )
    sys.exit(1)


def announce_server_action(message: str, url: str | None = None) -> str:
    """Log an info message that includes the active server URL and return it."""
    url = url or require_active_server()
    console.info(f"{message} [cyan]{url}[/cyan]")
    return url


async def confirm_server_action(message: str, url: str | None = None, *, yes: bool = False) -> None:
    """Ask for confirmation before continuing with an action on the active server."""
    if yes:
        return
    url = url or require_active_server()
    confirmed = await inquirer.confirm(message=f"{message} {url}?", default=False).execute_async()
    if not confirmed:
        console.info("Action cancelled.")
        sys.exit(1)
