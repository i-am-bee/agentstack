# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import re
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
import agentstack_cli.commands.user
from agentstack_cli.async_typer import AliasGroup, AsyncTyper
from agentstack_cli.configuration import Configuration

logging.basicConfig(level=logging.INFO if Configuration().debug else logging.FATAL)
logging.getLogger("httpx").setLevel(logging.WARNING)  # not sure why this is necessary


class RootHelpGroup(AliasGroup):
    def get_help(self, ctx):
        return """\
Usage: agentstack [OPTIONS] COMMAND [ARGS]...

╭─ Getting Started ──────────────────────────────────────────────────────────╮
│ ui       Launch the web interface                                          │
│ list     View all available agents                                         │
│ run      Run an agent interactively                                        │
╰────────────────────────────────────────────────────────────────────────────╯

╭─ Agent Management ─────────────────────────────────────────────────────────╮
│ add                               Install an agent (Docker, GitHub)        │
│ remove                            Uninstall an agent                       │
│ update                            Update an agent                          │
│ info                              Show agent details                       │
│ logs                              Stream agent execution logs              │
│ env                               Manage agent environment variables       │
│ build                             Build an agent remotely                  │
│ client-side-build                 Build an agent container image locally   │
╰────────────────────────────────────────────────────────────────────────────╯

╭─ Platform & Configuration ─────────────────────────────────────────────────╮
│ model           Configure 15+ LLM providers                                │
│ platform        Start, stop, or delete local platform                      │
│ server          Connect to remote Agent Stack servers                      │
│ user            Manage users and roles                                     │
│ self version    Show Agent Stack CLI and Platform version                  │
│ self upgrade    Upgrade Agent Stack CLI and Platform                       │
│ self uninstall  Uninstall Agent Stack CLI and Platform                     │
╰────────────────────────────────────────────────────────────────────────────╯

╭─ Options ──────────────────────────────────────────────────────────────────╮
│ --help                Show this help message                               │
│ --show-completion     Show tab completion script                           │
│ --install-completion  Enable tab completion for commands                   │
╰────────────────────────────────────────────────────────────────────────────╯
"""


app = AsyncTyper(no_args_is_help=True, cls=RootHelpGroup)
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
app.add_typer(
    agentstack_cli.commands.user.app,
    name="user",
    no_args_is_help=True,
    help="Manage users.",
)


agent_alias = deepcopy(agentstack_cli.commands.agent.app)
for cmd in agent_alias.registered_commands:
    cmd.rich_help_panel = "Agent commands"

app.add_typer(agent_alias, name="", no_args_is_help=True)


@app.command("version")
async def version(
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
):
    """Print version of the Agent Stack CLI."""
    import agentstack_cli.commands.self

    await agentstack_cli.commands.self.version(verbose=verbose)


@app.command("ui")
async def ui():
    """Launch the graphical interface."""
    import webbrowser

    import agentstack_cli.commands.model

    await agentstack_cli.commands.model.ensure_llm_provider()

    config = Configuration()
    active_server = config.auth_manager.active_server

    if active_server:
        if re.search(r"(localhost|127\.0\.0\.1):8333", active_server):
            ui_url = re.sub(r":8333", ":8334", active_server)
        else:
            ui_url = active_server
    else:
        ui_url = "http://localhost:8334"

    webbrowser.open(ui_url)


if __name__ == "__main__":
    app()
