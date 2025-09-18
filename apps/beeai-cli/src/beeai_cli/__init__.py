# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import typing
from copy import deepcopy

import typer

import beeai_cli.commands.agent
import beeai_cli.commands.build
import beeai_cli.commands.mcp
import beeai_cli.commands.model
import beeai_cli.commands.platform
import beeai_cli.commands.self
import beeai_cli.commands.server
from beeai_cli.async_typer import AsyncTyper
from beeai_cli.configuration import Configuration

logging.basicConfig(level=logging.INFO if Configuration().debug else logging.FATAL)
logging.getLogger("httpx").setLevel(logging.WARNING)  # not sure why this is necessary

app = AsyncTyper(no_args_is_help=True)
app.add_typer(beeai_cli.commands.model.app, name="model", no_args_is_help=True, help="Manage model providers.")
app.add_typer(beeai_cli.commands.agent.app, name="agent", no_args_is_help=True, help="Manage agents.")
app.add_typer(beeai_cli.commands.platform.app, name="platform", no_args_is_help=True, help="Manage BeeAI platform.")
app.add_typer(beeai_cli.commands.mcp.app, name="mcp", no_args_is_help=True, help="Manage MCP servers and toolkits.")
app.add_typer(beeai_cli.commands.build.app, name="", no_args_is_help=True, help="Build agent images.")
app.add_typer(
    beeai_cli.commands.server.app, name="server", no_args_is_help=True, help="Manage BeeAI servers and authentication."
)
app.add_typer(
    beeai_cli.commands.self.app, name="self", no_args_is_help=True, help="Manage BeeAI installation.", hidden=True
)


agent_alias = deepcopy(beeai_cli.commands.agent.app)
for cmd in agent_alias.registered_commands:
    cmd.rich_help_panel = "Agent commands"

app.add_typer(agent_alias, name="", no_args_is_help=True)


@app.command("version")
async def version(verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False):
    """Print version of the BeeAI CLI."""
    import beeai_cli.commands.self

    await beeai_cli.commands.self.version(verbose=verbose)


@app.command("ui")
async def ui():
    """Launch the graphical interface."""
    import webbrowser

    import beeai_cli.commands.model

    await beeai_cli.commands.model.ensure_llm_provider()
    webbrowser.open(
        "http://localhost:8334"
    )  # TODO: This always opens the local UI, how to open the UI of a logged in server instead?


if __name__ == "__main__":
    app()
