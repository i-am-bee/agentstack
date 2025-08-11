# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import webbrowser

from beeai_cli.api import api_request
from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.configuration import Configuration
from beeai_cli.token_store import clear_token, save_token

app = AsyncTyper()

config = Configuration()
BASE_URL = str(config.host).rstrip("/")
API_BASE_URL = f"{BASE_URL}/api/v1/"
LOGIN_URL = f"{API_BASE_URL}login"
CALLBACK_URL = f"{API_BASE_URL}display-passcode"
TOKEN_PATH = os.path.expanduser("~/.beeai_token")


@app.command("login")
async def cli_login():
    """
    Login to BeeAI using the default browser (OIDC flow).
    """
    login_url = f"{LOGIN_URL}?callback_url={CALLBACK_URL}"

    console.print("[bold green]API endpoint:[/bold green] http://localhost:18333")
    console.print(f"\n[bold yellow]Get a one-time code from:[/bold yellow] {login_url}")

    # Prompt to open browser
    choice = input("Open the URL in the default browser? [Y/n] > ").strip().lower()
    if choice in ["", "y", "yes"]:
        webbrowser.open(login_url)
    else:
        console.print("Please open the above URL manually in your browser.")

    passcode = input("Press [Enter] one-time passcode > ")

    console.print("\nAuthenticating...")
    for _ in range(60):
        await asyncio.sleep(1)
        poll_resp = await api_request("GET", "token", params={"passcode": str(passcode)}, use_auth=False)
        if poll_resp and "token" in poll_resp:
            await save_token(poll_resp["token"])
            console.print("\n[bold green]Ok! Login successful.[/bold green]")
            return
    console.print("\n [bold red] Login timed out or not successful. [/bold red] ")
    raise RuntimeError("Login failed.")


@app.command("logout")
async def cli_logout():
    """
    Logout to BeeAI.
    """
    await clear_token()
    console.print("Logout successful!")
