# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import sys
import typing

import pydantic
import typer
from agentstack_sdk.platform.connector import Connector, ConnectorState
from agentstack_sdk.platform.types import Metadata
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from agentstack_cli import configuration
from agentstack_cli.async_typer import AsyncTyper
from agentstack_cli.configuration import Configuration
from agentstack_cli.console import console
from agentstack_cli.server_utils import (
    announce_server_action,
    confirm_server_action,
)

app = AsyncTyper()
config = Configuration()


@app.command("create")
async def create_connector(
    url: typing.Annotated[str, typer.Argument(help="Agent location (public docker image or github url)")],
    client_id: typing.Annotated[
        str | None,
        typer.Option("--client-id", help="Client ID for authentication, acquired from env if not supplied"),
    ] = None,
    client_secret: typing.Annotated[
        str | None,
        typer.Option("--client-secret", help="Client secret for authentication, acquired from env if not supplied"),
    ] = None,
    metadata: typing.Annotated[str | None, typer.Option("--metadata", help="Metadata as JSON string")] = None,
    match_preset: typing.Annotated[
        bool, typer.Option("--match-preset", help="Use preset configuration for given url if it exists")
    ] = True,
) -> None:
    """Create a connector to an external service."""
    async with configuration.use_platform_client():
        connector = await Connector.create(
            url,
            client_id=client_id if client_id else config.client_id,
            client_secret=client_secret if client_secret else config.client_secret,
            metadata=pydantic.TypeAdapter(Metadata).validate_json(metadata if metadata else "{}"),
            match_preset=match_preset,
        )
        console.success(
            f"Created connector for URL [blue]{connector.url}[/blue] with id: [green]{connector.id}[/green]\n"
            f"Connector status: [yellow]{connector.state}[/yellow]"
        )


def search_path_match_connectors(search_path: str, connectors: list[Connector]) -> list[Connector]:
    return [
        c for c in connectors if (search_path in str(c.id) or search_path.lower() in c.url.unicode_string().lower())
    ]


async def select_connectors_multi(
    search_path: str, connectors: list[Connector], operation_name: str = "remove"
) -> list[Connector]:
    """Select multiple connectors matching the search path."""
    connector_candidates = search_path_match_connectors(search_path, connectors)
    if not connector_candidates:
        raise ValueError(f"No matching connectors found for '{search_path}'")

    if len(connector_candidates) == 1:
        return connector_candidates

    # Multiple matches - show selection menu
    choices = [Choice(value=c, name=f"{c.url} - {c.id} ({c.state})") for c in connector_candidates]

    selected_connectors = await inquirer.checkbox(
        message=f"Select connectors to {operation_name} (use ↑/↓ to navigate, Space to select):", choices=choices
    ).execute_async()

    return selected_connectors or []


@app.command("remove | rm | delete")
async def remove_connector(
    search_path: typing.Annotated[
        str, typer.Argument(help="Short ID or connector url, supports partial matching")
    ] = "",
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
    all: typing.Annotated[bool, typer.Option("--all", "-a", help="Remove all connectors without selection.")] = False,
) -> None:
    """Remove connectors."""

    async def _delete_and_wait_for_completion(connector: Connector) -> None:
        await connector.delete()
        await connector.wait_for_deletion()

    if search_path and all:
        console.error(
            "[red]Cannot specify both --all and a search path. Use --all to remove all connectors, or provide a search path for specific connectors.[/red]"
        )
        sys.exit(1)

    async with configuration.use_platform_client():
        connectors_list = await Connector.list()
        connectors = connectors_list.items
        if len(connectors) == 0:
            console.info("[yellow]No connectors found.[/yellow]")
            return

        if all:
            selected_connectors = connectors
        else:
            selected_connectors = await select_connectors_multi(search_path, connectors, operation_name="remove")

        if not selected_connectors:
            console.info("[yellow]No connectors selected, exiting.[/yellow]")
            return
        else:
            connector_names = "\n".join([f"  - {c.url} - {c.id}" for c in selected_connectors])

        message = f"\n[bold]Selected connectors to remove:[/bold]\n{connector_names}\n from "

        url = announce_server_action(message)
        await confirm_server_action("Proceed with removing these connectors from", url=url, yes=yes)

        with console.status("Removing connector(s)...", spinner="dots"):
            delete_tasks = [_delete_and_wait_for_completion(connector) for connector in selected_connectors]
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)

        # Check results for exceptions
        successful_deletions = []
        for connector, result in zip(selected_connectors, results, strict=True):
            if isinstance(result, Exception):
                console.error(f"[red]Failed to delete {connector.url}:[/red] {result}")
            else:
                successful_deletions.append(connector)

        # Wait for successful deletions to complete
        for connector in successful_deletions:
            console.success(f"[green]Successfully deleted connector {connector.url}[/green]")


@app.command("list")
async def list_connectors() -> None:
    """List all connectors."""
    async with configuration.use_platform_client():
        connectors = await Connector.list()
        message = f"Found [green]{connectors.total_count}[/green] connectors"
        if connectors.total_count > 0:
            message += ":"
        for item in connectors.items:
            message += f"\n- {item.id}: {item.url} ({item.state})"

    console.success(message)


@app.command("list-presets")
async def list_connector_presets() -> None:
    """List connector presets."""
    async with configuration.use_platform_client():
        presets = await Connector.presets()
        message = f"Found [green]{presets.total_count}[/green] connector presets:"
        for item in presets.items:
            message += f"\n- {item}"

    console.success(message)


def find_matching_connector(search_path: str, connectors: list[Connector]) -> Connector:
    connector_candidates = search_path_match_connectors(search_path, connectors)
    if len(connector_candidates) != 1:
        message = f"Found {len(connector_candidates)} matching connectors"
        connector_list = [f"  - {c.url} - {c.id} ({c.state})" for c in connector_candidates]
        connectors_detail = ":\n" + "\n".join(connector_list) if connector_list else ""
        raise ValueError(message + connectors_detail)
    [selected_connector] = connector_candidates
    return selected_connector


async def select_connector(search_path: str) -> Connector | None:
    connectors_list = await Connector.list()
    connectors = connectors_list.items
    if connectors_list.total_count == 0:
        console.info("[yellow]No connectors found.[/yellow]")
        return

    try:
        selected_connector = find_matching_connector(search_path, connectors)
        return selected_connector
    except ValueError as e:
        console.error(e.__str__())
        console.hint("Please refine your input to match exactly one connector id or url.")
        sys.exit(1)


@app.command("get")
async def get_connector(
    search_path: typing.Annotated[str, typer.Argument(help="Short ID or connector url, supports partial matching")],
) -> None:
    """Get connector details."""
    async with configuration.use_platform_client():
        selected_connector = await select_connector(search_path)
        if not selected_connector:
            return

        connector = await Connector.get(selected_connector.id)
        connector_data = connector.model_dump()
        message = "Connector details:"
        for key, value in connector_data.items():
            if key in ["auth_request"]:
                continue  # Skip auth_request details
            message += f"\n- {key}: {value}"

    console.success(message)


@app.command("connect")
async def connect(
    search_path: typing.Annotated[str, typer.Argument(help="Short ID or connector url, supports partial matching")],
) -> None:
    """Connect a connector (e.g., start OAuth flow)."""
    async with configuration.use_platform_client():
        selected_connector = await select_connector(search_path)
        if not selected_connector:
            return

        try:
            with console.status("Connecting connector...", spinner="dots"):
                connector = await selected_connector.connect()
                connector = await connector.wait_for_state(state=ConnectorState.connected)

            console.success(
                f"[green]Connector connected successfully:[/green] {connector.url} (state: {connector.state})"
            )
        except Exception as e:
            console.error(f"[red]Failed to connect connector:[/red] {e}")
            raise typer.Exit(code=1) from None


@app.command("disconnect")
async def disconnect(
    search_path: typing.Annotated[
        str, typer.Argument(help="Short ID or connector url, supports partial matching")
    ] = "",
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
    all: typing.Annotated[
        bool, typer.Option("--all", "-a", help="Deisconnect all connectors without selection.")
    ] = False,
) -> None:
    """Disconnect one or more connectors."""

    async def _discionnect_and_wait_for_completion(connector: Connector) -> None:
        await connector.disconnect()
        await connector.wait_for_state(state=ConnectorState.disconnected)

    if search_path and all:
        console.error(
            "[red]Cannot specify both --all and a search path. Use --all to remove all connectors, or provide a search path for specific connectors.[/red]"
        )
        sys.exit(1)

    async with configuration.use_platform_client():
        connectors_list = await Connector.list()
        connectors = connectors_list.items
        if len(connectors) == 0:
            console.info("[yellow]No connectors found.[/yellow]")
            return

        if all:
            selected_connectors = connectors
        else:
            selected_connectors = await select_connectors_multi(search_path, connectors, operation_name="disconnect")

        if not selected_connectors:
            console.info("[yellow]No connectors selected, exiting.[/yellow]")
            return
        else:
            connector_names = "\n".join([f"  - {c.url} - {c.id}" for c in selected_connectors])

        message = f"\n[bold]Selected connectors to disconnect:[/bold]\n{connector_names}\n from "

        url = announce_server_action(message)
        await confirm_server_action("Proceed with disconnecting these connectors from", url=url, yes=yes)

        with console.status("Disconnecting connectors...", spinner="dots"):
            disconnect_tasks = [_discionnect_and_wait_for_completion(connector) for connector in selected_connectors]
            results = await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # Check results for exceptions
        successful_disconnections = []
        for connector, result in zip(selected_connectors, results, strict=True):
            if isinstance(result, Exception):
                console.error(f"[red]Failed to disconnect {connector.url}:[/red] {result}")
                console.hint("Check that the selected connector is currently connected.")
            else:
                successful_disconnections.append(connector)

        # Wait for successful disconnections to complete
        for connector in successful_disconnections:
            console.success(f"[green]Successfully disconnected connector[/green] {connector.url}")
