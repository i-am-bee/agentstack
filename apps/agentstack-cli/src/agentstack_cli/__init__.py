# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import typing
from copy import deepcopy

import typer

import agentstack_cli.commands.agent
import agentstack_cli.commands.build
import agentstack_cli.commands.mcp
import agentstack_cli.commands.model
import agentstack_cli.commands.platform
import agentstack_cli.commands.self
import agentstack_cli.commands.server
from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.configuration import Configuration

logging.basicConfig(level=logging.INFO if Configuration().debug else logging.FATAL)
logging.getLogger("httpx").setLevel(logging.WARNING)  # not sure why this is necessary

app = AsyncTyper(no_args_is_help=True)
app.add_typer(agentstack_cli.commands.model.app, name="model", no_args_is_help=True, help="Manage model providers.")
app.add_typer(agentstack_cli.commands.agent.app, name="agent", no_args_is_help=True, help="Manage agents.")
app.add_typer(
    agentstack_cli.commands.platform.app, name="platform", no_args_is_help=True, help="Manage Agent Stack platform."
)
app.add_typer(
    agentstack_cli.commands.mcp.app, name="mcp", no_args_is_help=True, help="Manage MCP servers and toolkits."
)
app.add_typer(agentstack_cli.commands.build.app, name="", no_args_is_help=True, help="Build agent images.")
app.add_typer(
    agentstack_cli.commands.server.app,
    name="server",
    no_args_is_help=True,
    help="Manage Agent Stack servers and authentication.",
)
app.add_typer(
    agentstack_cli.commands.self.app,
    name="self",
    no_args_is_help=True,
    help="Manage Agent Stack installation.",
    hidden=True,
)


agent_alias = deepcopy(agentstack_cli.commands.agent.app)
for cmd in agent_alias.registered_commands:
    cmd.rich_help_panel = "Agent commands"

app.add_typer(agent_alias, name="", no_args_is_help=True)


@app.command("version")
async def version(verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False):
    """Print version of the Agent Stack CLI."""
    import agentstack_cli.commands.self

    await agentstack_cli.commands.self.version(verbose=verbose)


@app.command("ui")
async def ui():
    """Launch the graphical interface."""
    import webbrowser

    import agentstack_cli.commands.model

    await agentstack_cli.commands.model.ensure_llm_provider()
    webbrowser.open(
        "http://localhost:8334"
    )  # TODO: This always opens the local UI, how to open the UI of a logged in server instead?


if __name__ == "__main__":
    app()
