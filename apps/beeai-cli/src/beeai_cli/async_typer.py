# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import functools
import inspect
import re
from collections.abc import Iterator
from contextlib import contextmanager

import rich.text
import typer
from rich.console import RenderResult
from rich.markdown import Heading, Markdown
from rich.table import Table
from typer.core import TyperGroup

from beeai_cli.configuration import Configuration
from beeai_cli.console import console, err_console
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
                    if inspect.iscoroutinefunction(f):
                        return asyncio.run(f(*args, **kwargs))
                    else:
                        return f(*args, **kwargs)
                except* Exception as ex:
                    for exc_type, message in extract_messages(ex):
                        err_console.print(format_error(exc_type, message))
                        if exc_type in ["ConnectionError", "ConnectError"]:
                            err_console.print(
                                "💡 [yellow]HINT[/yellow]: Start the BeeAI platform using: [green]beeai platform start[/green]. If that does not help, run [green]beeai platform delete[/green] to start with a clean slate, then try [green]beeai platform start[/green] again."
                            )
                        elif exc_type == "McpError":
                            err_console.print(
                                "💡 [yellow]HINT[/yellow]: Is your configuration correct? Try re-entering your LLM API details with: [green]beeai env setup[/green]"
                            )
                        else:
                            err_console.print(
                                "💡 [yellow]HINT[/yellow]: Are you having consistent problems? If so, try these troubleshooting steps: [green]beeai platform delete[/green] to remove the platform, and [green]beeai platform start[/green] to recreate it."
                            )
                    if DEBUG:
                        raise

            parent_decorator(wrapped_f)
            return f

        return decorator
