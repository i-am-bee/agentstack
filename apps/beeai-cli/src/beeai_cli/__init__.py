# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from copy import deepcopy

import beeai_cli.commands.agent
import beeai_cli.commands.build
import beeai_cli.commands.env
import beeai_cli.commands.platform
from beeai_cli.async_typer import AsyncTyper
from beeai_cli.configuration import Configuration
from beeai_cli.utils import launch_graphical_interface

logging.basicConfig(level=logging.INFO if Configuration().debug else logging.FATAL)

app = AsyncTyper(no_args_is_help=True)
app.add_typer(beeai_cli.commands.env.app, name="env", no_args_is_help=True, help="Manage environment variables.")
app.add_typer(beeai_cli.commands.agent.app, name="agent", no_args_is_help=True, help="Manage agents.")
app.add_typer(beeai_cli.commands.platform.app, name="platform", no_args_is_help=True, help="Manage BeeAI platform.")
app.add_typer(beeai_cli.commands.build.app, name="", no_args_is_help=True, help="Build agent images.")


agent_alias = deepcopy(beeai_cli.commands.agent.app)
for cmd in agent_alias.registered_commands:
    cmd.rich_help_panel = "Agent commands"

app.add_typer(agent_alias, name="", no_args_is_help=True)


@app.command("version")
def show_version():
    """Print version of the BeeAI CLI."""
    from importlib.metadata import version

    print("beeai-cli version:", version("beeai-cli"))


@app.command("ui")
async def ui():
    """Launch graphical interface."""
    host_url = str(Configuration().host)

    await launch_graphical_interface(host_url)


@app.command("playground")
async def playground() -> None:
    """Launch the graphical interface for the compose playground."""
    config = Configuration()
    host_url = str(config.host) + str(config.playground)

    await launch_graphical_interface(host_url)


if __name__ == "__main__":
    app()
