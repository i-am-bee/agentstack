# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing
from datetime import datetime

import typer
from agentstack_sdk.platform import User
from agentstack_sdk.platform.user import UserRole
from rich.table import Column

from agentstack_cli.async_typer import AsyncTyper, console, create_table
from agentstack_cli.configuration import Configuration
from agentstack_cli.utils import announce_server_action, confirm_server_action

app = AsyncTyper()
configuration = Configuration()

ROLE_DISPLAY = {
    "admin": "[red]admin[/red]",
    "developer": "[cyan]developer[/cyan]",
    "user": "user",
}


@app.command("list")
async def list_users(
    email: typing.Annotated[str | None, typer.Option(help="Filter by email (case-insensitive partial match)")] = None,
    limit: typing.Annotated[int, typer.Option(help="Results per page (1-100)")] = 40,
    after: typing.Annotated[str | None, typer.Option(help="Pagination cursor (page_token)")] = None,
):
    """List platform users (admin only)."""
    announce_server_action("Listing users on")

    async with configuration.use_platform_client():
        result = await User.list(email=email, limit=limit, page_token=after)

        items = result.items
        has_more = result.has_more
        next_page_token = result.next_page_token

    with create_table(
        Column("ID", style="yellow"),
        Column("Email"),
        Column("Role"),
        Column("Created"),
        Column("Role Updated"),
        no_wrap=True,
    ) as table:
        for user in items:
            role_display = ROLE_DISPLAY.get(user.role, user.role)

            created_at = _format_date(user.created_at)
            role_updated_at = _format_date(user.role_updated_at) if user.role_updated_at else "-"

            table.add_row(
                user.id,
                user.email,
                role_display,
                created_at,
                role_updated_at,
            )

    console.print()
    console.print(table)

    if has_more and next_page_token:
        console.print(f"\n[dim]Use --after {next_page_token} to see more[/dim]")


@app.command("set-role")
async def set_role(
    user_id: typing.Annotated[str, typer.Argument(help="User UUID")],
    role: typing.Annotated[UserRole, typer.Argument(help="Target role (admin, developer, user)")],
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
):
    """Change user role (admin only)."""
    url = announce_server_action(f"Changing user {user_id} to role '{role}' on")
    await confirm_server_action("Proceed with role change on", url=url, yes=yes)

    async with configuration.use_platform_client():
        result = await User.set_role(user_id, UserRole(role))

        role_display = ROLE_DISPLAY.get(result.new_role, result.new_role)

        console.success(f"User role updated to [cyan]{role_display}[/cyan]")


def _format_date(dt: datetime | None) -> str:
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M")
