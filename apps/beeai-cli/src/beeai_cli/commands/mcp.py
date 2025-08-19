# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing
from enum import StrEnum

import typer
from rich.table import Column

from beeai_cli.api import api_request
from beeai_cli.async_typer import AsyncTyper, console, create_table
from beeai_cli.utils import (
    status,
)

app = AsyncTyper()


class Transport(StrEnum):
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


@app.command("add")
async def add_provider(
    name: typing.Annotated[str, typer.Argument(help="Name for the MCP server")],
    location: typing.Annotated[str, typer.Argument(help="Location of the MCP server")],
    transport: typing.Annotated[
        Transport, typer.Argument(help="Transport the MCP server uses")
    ] = Transport.STREAMABLE_HTTP,
) -> None:
    """Install discovered MCP server."""

    with status("Registering server to platform"):
        await api_request(
            "POST", "mcp/providers", json={"name": name, "location": location, "transport": transport.value}
        )
    console.print("Registering server to platform [[green]DONE[/green]]")
    await list_providers()


@app.command("list")
async def list_providers():
    """List MCP servers."""

    providers = await api_request("GET", "mcp/providers")
    assert providers
    with create_table(
        Column("Name"),
        Column("Location"),
        Column("Transport"),
        Column("State"),
        no_wrap=True,
    ) as table:
        for provider in providers:
            table.add_row(provider["name"], provider["location"], provider["transport"], provider["state"])
    console.print()
    console.print(table)


@app.command("remove | uninstall | rm | delete")
async def uninstall_provider(
    name: typing.Annotated[str, typer.Argument(help="Name of the MCP provider to remove")],
) -> None:
    """Remove MCP server."""
    provider = await _get_provider_by_name(name)
    if provider:
        await api_request("delete", f"mcp/providers/{provider['id']}")
    else:
        raise ValueError(f"Provider {name} not found")
    await list_providers()


tool_app = AsyncTyper()
app.add_typer(tool_app, name="tool", no_args_is_help=True, help="Inspect tools.")


@tool_app.command("list")
async def list_tools() -> None:
    """List tools."""

    tools = await api_request("GET", "mcp/tools")
    assert tools
    with create_table(
        Column("Name"),
        Column("Description", max_width=30),
        no_wrap=True,
    ) as table:
        for tool in tools:
            table.add_row(tool["name"], tool["description"])
    console.print()
    console.print(table)


toolkit_app = AsyncTyper()
app.add_typer(toolkit_app, name="toolkit", no_args_is_help=True, help="Create toolkits.")


@toolkit_app.command("create")
async def toolkit(
    tools: typing.Annotated[list[str], typer.Argument(help="Tools to put in the toolkit")],
) -> None:
    """Create a toolkit."""

    api_tools = await _get_tools_by_names(tools)
    assert api_tools
    toolkit = await api_request("POST", "mcp/toolkits", json={"tools": [tool["id"] for tool in api_tools]})
    assert toolkit
    with create_table(Column("Location"), Column("Transport"), Column("Expiration")) as table:
        table.add_row(toolkit["location"], toolkit["transport"], toolkit["expires_at"])
    console.print()
    console.print(table)


async def _get_provider_by_name(name: str):
    providers = await api_request("GET", "mcp/providers")
    assert providers

    for provider in providers:
        if provider["name"] == name:
            return provider

    raise ValueError(f"Provider {name} not found")


async def _get_tools_by_names(names: list[str]) -> list[dict[str, typing.Any]]:
    all_tools = await api_request("GET", "mcp/tools")
    assert all_tools

    tools = []
    for name in names:
        found = False
        for tool in all_tools:
            if tool["name"] == name:
                tools.append(tool)
                found = True
                break
        if not found:
            raise ValueError(f"Tool {name} not found")

    return tools
