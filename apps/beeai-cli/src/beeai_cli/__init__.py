# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from copy import deepcopy

from beeai_cli.configuration import Configuration
import beeai_cli.commands.agent
import beeai_cli.commands.build
import beeai_cli.commands.env
import beeai_cli.commands.platform
from beeai_cli.async_typer import AsyncTyper
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
    """Print version of the BeeAI CLI and related libraries."""
    from importlib.metadata import version

    print("beeai-cli version:", version("beeai-cli"))
    print("beeai-server version:", version("beeai-server"))
    print("acp-sdk version:", version("acp-sdk"))


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
