# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.configuration import Configuration

app = AsyncTyper()

config = Configuration()


@app.command("show")
def show_server():
    active = config.auth_manager.get_active_resource()
    if not active:
        console.print("No active server!!!\n")
        return
    console.print(f"Active server: {active}\n")


@app.command("list")
def list_server():
    resources = config.auth_manager.config.get("resources", {})
    if not resources:
        console.print("No servers logged in. Run `beeai login` first.\n")
        return
    console.print("Known servers:")
    for res in resources:
        marker = " (active)" if res == config.auth_manager.get_active_resource() else ""
        console.print(f"{res}{marker}\n")


@app.command("switch")
def switch_server():
    resources = config.auth_manager.config.get("resources", {})
    if not resources:
        console.print("No server logged in. Run `beeai login` first.\n")

    resource_names = list(resources.keys())

    console.print("Available servers:")
    for i, res in enumerate(resources, start=1):
        marker = " (active)" if res == config.auth_manager.get_active_resource() else ""
        console.print(f"{i}. {res}{marker}")

    choice = input("Select a server number: ")
    try:
        idx = int(choice)
    except ValueError:
        raise ValueError("Invalid choice") from None

    if 1 <= idx <= len(resource_names):
        resource_name = resource_names[idx - 1]
        resource_data = resources[resource_name]
        auth_servers = list(resource_data.get("authorization_servers", {}).keys())

        if not auth_servers:
            console.print(
                f"No tokens available for {resource_name}. You may need to run `beeai login -- {resource_name}`."
            )
            return
        if len(auth_servers) == 1:
            issuer = auth_servers[0]
        else:
            console.print("Multiple authorization servers are available.\n")
            for j, issuer in enumerate(auth_servers, start=1):
                marker = (
                    " [active]"
                    if (
                        resource_name == config.auth_manager.config.get("active_resource")
                        and issuer == config.auth_manager.config.get("active_token")
                    )
                    else ""
                )
                console.print(f"{j}. {issuer}{marker}")
            choice = input("\nSelect an authorization server: ").strip()
            if not choice:
                choice = "1"
            try:
                issuer = auth_servers[int(choice) - 1]
            except (ValueError, IndexError):
                raise ValueError("Invalid choice") from None

        config.auth_manager.set_active_resource(resource_name)
        config.auth_manager.set_active_token(resource_name, issuer)

        console.print(f"Switched resource to: {resource_name}")
