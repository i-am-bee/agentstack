# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import json
import typing
from uuid import UUID

import pydantic
import typer
from agentstack_sdk.platform.client import PlatformClient
from agentstack_sdk.platform.connector import Connector, ConnectorState
from agentstack_sdk.platform.types import Metadata
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from agentstack_cli import configuration
from agentstack_cli.async_typer import AsyncTyper, console
from agentstack_cli.configuration import Configuration
from agentstack_cli.utils import (
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
        typer.Option("--client-id", "-cid", help="Client ID for authentication, acquired form env if not supplied"),
    ] = None,
    client_secret: typing.Annotated[
        str | None,
        typer.Option(
            "--client-secret", "-cs", help="Client secret for authentication, acquired form env if not supplied"
        ),
    ] = None,
    metadata: typing.Annotated[str | None, typer.Option("--metadata", "-md", help="Metadata as JSON string")] = None,
    match_preset: typing.Annotated[
        bool, typer.Option("--match-preset", "-mp", help="Use preset configuration for given url if it exists")
    ] = True,
) -> None:
    """Create a connector to an external service."""
    try:
        metadata_dict = json.loads(metadata) if isinstance(metadata, str) else {}
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing metadata JSON:[/red] {e}")
        raise typer.Exit(code=1) from None
    async with configuration.use_platform_client() as client:
        connector = await Connector.create(
            url,
            client_id=client_id if client_id else config.client_id,
            client_secret=client_secret if client_secret else config.client_secret,
            metadata=pydantic.TypeAdapter(Metadata).validate_python(metadata_dict),
            match_preset=match_preset,
            client=client,
        )
        console.print(f"Created connector for URL [blue]{connector.url}[/blue] with id: [green]{connector.id}[/green]")
        console.print(f"Connector status: [yellow]{connector.state}[/yellow]")


def search_path_match_connectors(search_path: str, connectors: list[Connector]) -> dict[UUID, Connector]:
    return {
        c.id: c
        for c in connectors
        if (search_path in str(c.id) or search_path.lower() in c.url.unicode_string().lower())
    }


async def select_connectors_multi(search_path: str, connectors: list[Connector]) -> list[Connector]:
    """Select multiple connectors matching the search path."""
    connector_candidates = search_path_match_connectors(search_path, connectors)
    if not connector_candidates:
        raise ValueError(f"No matching connectors found for '{search_path}'")

    if len(connector_candidates) == 1:
        return list(connector_candidates.values())

    # Multiple matches - show selection menu
    choices = [Choice(value=c.id, name=f"{c.url} - {c.id} ({c.state})") for c in connector_candidates.values()]

    selected_ids = await inquirer.checkbox(  # pyright: ignore[reportPrivateImportUsage]
        message="Select connectors to remove (use ↑/↓ to navigate, Space to select):", choices=choices
    ).execute_async()

    return [connector_candidates[cid] for cid in (selected_ids or [])]


@app.command("remove | rm | delete")
async def remove_connector(
    search_path: typing.Annotated[
        str, typer.Argument(help="Short ID or connector url, supports partial matching")
    ] = "",
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
    all: typing.Annotated[bool, typer.Option("--all", "-a", help="Remove all connectors without selection.")] = False,
) -> None:
    """Remove connectors."""

    async def _delete_and_wait_for_completion(connector: Connector, client: PlatformClient) -> None:
        await connector.delete(client=client)
        await connector.wait_for_deletion(client=client)

    if search_path and all:
        console.print(
            "[red]Cannot specify both --all and a search path."
            " Use --all to remove all connectors, or provide a search path for specific connectors."
            "[/red]"
        )
        raise typer.Exit(1)

    async with configuration.use_platform_client() as client:
        connectors_list = await Connector.list(client=client)
        connectors = connectors_list.items
        if len(connectors) == 0:
            console.print("[yellow]No connectors found.[/yellow]")
            return

        if all:
            selected_connectors = connectors
        else:
            selected_connectors = await select_connectors_multi(search_path, connectors)

        if not selected_connectors:
            console.print("[yellow]No connectors selected, exiting.[/yellow]")
            return
        else:
            connector_names = "\n".join([f"  - {c.url} - {c.id}" for c in selected_connectors])

        message = f"\n[bold]Selected connectors to remove:[/bold]\n{connector_names}\n from "

        url = announce_server_action(message)
        await confirm_server_action("Proceed with removing these connectors from", url=url, yes=yes)

        with console.status("Removing connector(s)...", spinner="dots"):
            delete_tasks = [_delete_and_wait_for_completion(connector, client) for connector in selected_connectors]
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)

        # Check results for exceptions
        successful_deletions = []
        for connector, result in zip(selected_connectors, results, strict=True):
            if isinstance(result, Exception):
                console.print(f"[red]Failed to delete {connector.url}:[/red] {result}")
            else:
                successful_deletions.append(connector)

        # Wait for successful deletions to complete
        for connector in successful_deletions:
            console.print(f"[green]Successfully deleted connector {connector.url}[/green]")


@app.command("list")
async def list_connectors() -> None:
    """List all connectors."""
    async with configuration.use_platform_client() as client:
        connectors = await Connector.list(client=client)
        message = f"Found [green]{connectors.total_count}[/green] connectors"
        if connectors.total_count > 0:
            message += ":"
        console.print(message)
        for item in connectors.items:
            console.print(f"- {item.id}: {item.url} ({item.state})")


@app.command("list-presets")
async def list_connector_presets() -> None:
    """List connector presets."""
    async with configuration.use_platform_client() as client:
        presets = await Connector.presets(client=client)
        console.print(f"Found [green]{presets.total_count}[/green] connector presets:")
        for item in presets.items:
            console.print(f"- {item}")


def find_matching_connector(search_path: str, connectors: list[Connector]) -> Connector:
    connector_candidates = search_path_match_connectors(search_path, connectors)
    if len(connector_candidates) != 1:
        connector_list = [f"  - {c.url} - {c.id} ({c.state})" for c in connector_candidates.values()]
        connectors_detail = ":\n" + "\n".join(connector_list) if connector_list else ""
        raise ValueError(f"{len(connector_candidates)} matching connectors{connectors_detail}")
    [selected_connector] = connector_candidates.values()
    return selected_connector


async def select_connector(search_path: str, client: PlatformClient) -> Connector | None:
    connectors_list = await Connector.list(client=client)
    connectors = connectors_list.items
    if connectors_list.total_count == 0:
        console.print("[yellow]No connectors found.[/yellow]")
        return

    try:
        selected_connector = find_matching_connector(search_path, connectors)
        return selected_connector
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=1) from None


@app.command("get")
async def get_connector(
    search_path: typing.Annotated[str, typer.Argument(help="Short ID or connector url, supports partial matching")],
) -> None:
    """Get connector details."""
    async with configuration.use_platform_client() as client:
        selected_connector = await select_connector(search_path, client)
        if not selected_connector:
            return

        connector = await Connector.get(selected_connector.id, client=client)
        connector_data = connector.model_dump()
        console.print("Connector details:")
        for key, value in connector_data.items():
            if key in ["auth_request"]:
                continue  # Skip auth_request details
            console.print(f"- [blue]{key}[/blue]: {value}")


@app.command("connect")
async def connect(
    search_path: typing.Annotated[str, typer.Argument(help="Short ID or connector url, supports partial matching")],
) -> None:
    """Connect a connector (e.g., start OAuth flow)."""
    async with configuration.use_platform_client() as client:
        selected_connector = await select_connector(search_path, client)
        if not selected_connector:
            return

        try:
            with console.status("Connecting connector...", spinner="dots"):
                connector = await selected_connector.connect(client=client)
                connector = await connector.wait_for_state(state=ConnectorState.connected)

            console.print(
                f"[green]Connector connected successfully:[/green] {connector.url} (state: {connector.state})"
            )
        except Exception as e:
            console.print(f"[red]Failed to connect connector: {e}[/red]")
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

    async def _discionnect_and_wait_for_completion(connector: Connector, client: PlatformClient) -> None:
        await connector.disconnect(client=client)
        await connector.wait_for_state(state=ConnectorState.disconnected, client=client)

    if search_path and all:
        console.print(
            "[red]Cannot specify both --all and a search path."
            " Use --all to remove all connectors, or provide a search path for specific connectors."
            "[/red]"
        )
        raise typer.Exit(1)

    async with configuration.use_platform_client() as client:
        connectors_list = await Connector.list(client=client)
        connectors = connectors_list.items
        if len(connectors) == 0:
            console.print("[yellow]No connectors found.[/yellow]")
            return

        if all:
            selected_connectors = connectors
        else:
            selected_connectors = await select_connectors_multi(search_path, connectors)

        if not selected_connectors:
            console.print("[yellow]No connectors selected, exiting.[/yellow]")
            return
        else:
            connector_names = "\n".join([f"  - {c.url} - {c.id}" for c in selected_connectors])

        message = f"\n[bold]Selected connectors to disconnect:[/bold]\n{connector_names}\n from "

        url = announce_server_action(message)
        await confirm_server_action("Proceed with disconnecting these connectors from", url=url, yes=yes)

        with console.status("Disconnecting connectors...", spinner="dots"):
            disconnect_tasks = [
                _discionnect_and_wait_for_completion(connector, client) for connector in selected_connectors
            ]
            results = await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # Check results for exceptions
        successful_disconnections = []
        for connector, result in zip(selected_connectors, results, strict=True):
            if isinstance(result, Exception):
                console.print(f"[red]Failed to disconnect {connector.url}:[/red] {result}")
            else:
                successful_disconnections.append(connector)

        # Wait for successful disconnections to complete
        for connector in successful_disconnections:
            console.print(f"[green]Successfully disconnected connector {connector.url}[/green]")
