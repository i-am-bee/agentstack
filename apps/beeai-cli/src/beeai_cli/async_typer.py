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

import asyncio
import functools
import inspect
import re
from contextlib import contextmanager
from typing import Iterator

import rich.text
import typer
from httpx import ConnectError, RemoteProtocolError
from rich.console import RenderResult
from rich.markdown import Heading, Markdown
from rich.table import Table
from typer.core import TyperGroup

from beeai_cli.console import console, err_console
from beeai_cli.api import resolve_connection_error
from beeai_cli.configuration import Configuration
from beeai_cli.utils import extract_messages, format_error

DEBUG = Configuration().debug


class _LeftAlignedHeading(Heading):
    def __rich_console__(self, *args, **kwargs) -> RenderResult:
        for elem in super().__rich_console__(*args, **kwargs):
            if isinstance(elem, rich.text.Text):
                elem.justify = "left"
            yield elem


Markdown.elements["heading_open"] = _LeftAlignedHeading


@contextmanager
def create_table(*args, no_wrap: bool = True, **kwargs) -> Iterator[Table]:
    table = Table(*args, **kwargs, box=None, pad_edge=False, width=console.width, show_header=True)
    yield table
    for column in table.columns:
        column.no_wrap = no_wrap
        column.overflow = "ellipsis"
        column.header = column.header.upper()

    if not table.rows:
        table._render = lambda *args, **kwargs: [rich.text.Text("<No items found>", style="italic")]


class AliasGroup(TyperGroup):
    """Taken from https://github.com/fastapi/typer/issues/132#issuecomment-2417492805"""

    _CMD_SPLIT_P = re.compile(r" ?[,|] ?")

    def get_command(self, ctx, cmd_name):
        cmd_name = self._group_cmd_name(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _group_cmd_name(self, default_name):
        for cmd in self.commands.values():
            name = cmd.name
            if name and default_name in self._CMD_SPLIT_P.split(name):
                return name
        return default_name


class AsyncTyper(typer.Typer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, cls=AliasGroup)

    def command(self, *args, **kwargs):
        parent_decorator = super().command(*args, **kwargs)

        def decorator(f):
            @functools.wraps(f)
            def wrapped_f(*args, **kwargs):
                try:
                    for retries in range(2):
                        try:
                            if inspect.iscoroutinefunction(f):
                                return asyncio.run(f(*args, **kwargs))
                            else:
                                return f(*args, **kwargs)
                        except* (RemoteProtocolError, ConnectionError, ConnectError):
                            if retries == 0:
                                asyncio.run(resolve_connection_error())
                            else:
                                raise
                except* Exception as ex:
                    for exc_type, message in extract_messages(ex):
                        err_console.print(format_error(exc_type, message))
                        if exc_type == "McpError":
                            err_console.print(
                                "💡 [yellow]HINT[/yellow]: Is your configuration correct? Try re-entering your LLM API details with: [green]beeai env setup[/green]"
                            )
                    if DEBUG:
                        raise

            parent_decorator(wrapped_f)
            return f

        return decorator
