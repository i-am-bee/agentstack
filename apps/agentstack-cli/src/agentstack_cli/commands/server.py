# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import logging
import sys
import typing
import uuid
import webbrowser
from urllib.parse import urlencode

import httpx
import typer
import uvicorn
from authlib.common.security import generate_token
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from agentstack_cli.async_typer import AsyncTyper, console
from agentstack_cli.configuration import Configuration

app = AsyncTyper()

config = Configuration()

REDIRECT_URI = "http://localhost:9001/callback"


async def _wait_for_auth_code(port: int = 9001) -> str:
    code_future: asyncio.Future[str] = asyncio.Future()
    app = FastAPI()

    @app.get("/callback")
    async def callback(request: Request):
        code = request.query_params.get("code")
        if code and not code_future.done():
            code_future.set_result(code)
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Successful</title>
                <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 15%; }
                h1 { color: #2e7d32; }
                p { color: #555; }
                </style>
            </head>
            <body>
                <h1>Login successful!</h1>
                <p>You can safely close this tab and return to the Agent Stack CLI.</p>
            </body>
            </html>
            """,
            status_code=200,
        )

    server = uvicorn.Server(config=uvicorn.Config(app, host="127.0.0.1", port=port, log_level=logging.ERROR))

    async with asyncio.TaskGroup() as tg:
        tg.create_task(server.serve())
        code = await code_future
        server.should_exit = True

    return code


def get_unique_app_name() -> str:
    return f"Agent Stack CLI {uuid.uuid4()}"


@app.command("login | change | select | default | switch")
async def server_login(server: typing.Annotated[str | None, typer.Argument()] = None):
    """Login to a server or switch between logged in servers."""
    server = server or (
        await inquirer.select(
            message="Select a server, or log in to a new one:",
            choices=[
                *(
                    Choice(
                        name=f"{server} {'(active)' if server == config.auth_manager.active_server else ''}",
                        value=server,
                    )
                    for server in config.auth_manager.servers
                ),
                Choice(name="Log in to a new server", value=None),
            ],
            default=0,
        ).execute_async()
        if config.auth_manager.servers
        else None
    )
    server = server or await inquirer.text(message="Enter server URL:").execute_async()

    if not server:
        raise RuntimeError("No server selected. Action cancelled.")

    if "://" not in server:
        server = f"https://{server}"

    server = server.rstrip("/")

    check_token = True
    log_in_message = "No authentication tokens found for this server. Proceeding to log in."

    if server_data := config.auth_manager.get_server(server):
        console.info("Logging in to a previously logged in server.")
        auth_server = None
        auth_servers = list(server_data.authorization_servers.keys())

        oauth_metadata = None
        try:
            oauth_metadata = await config.auth_manager.fetch_oauth_protected_resource_metadata(server)
            oauth_metadata_auth_servers = oauth_metadata.get("authorization_servers", [])
            if oauth_metadata_auth_servers:
                # something might have changed on the server side since we last logged in
                # re-check that the auth servers we know about are still valid
                auth_servers = [as_ for as_ in auth_servers if as_ in oauth_metadata_auth_servers]
            else:
                # shortcut
                auth_servers = []
        except Exception as e:
            console.warning(
                f"Failed to fetch server auth metadata, continuing without validation of current auth servers: {e!s}"
            )
            # Continue with the current auth servers info, which might still be valid even if metadata fetching failed
            pass

        if not auth_servers:
            # Re-check in case auth was enabled (leads to new login) or disabled (just passes) after the latest login and auth info update.
            if oauth_metadata is None or not oauth_metadata.get("authorization_servers", []):
                # Keep backward-compatible behavior when metadata cannot be fetched.
                # This might lead to errors when the server actually requires auth but does not provide standard info; however, that is not expected
                config.auth_manager.active_server = server
                config.auth_manager.active_auth_server = None
                config.auth_manager.clear_auth_info(server)
                console.success(f"Logged in to [cyan]{server}[/cyan].")
                return

            log_in_message = "Authentication has been newly enabled for this server. Proceeding to log in."
            check_token = False  # Skip token validation since we know the server now requires auth newly and no auth info can be present

        elif len(auth_servers) == 1:
            auth_server = auth_servers[0]
        elif len(auth_servers) > 1:
            auth_server = await inquirer.select(
                message="Select an authorization server:",
                choices=[
                    Choice(
                        name=f"{auth_server} {'(active)' if auth_server == config.auth_manager.active_auth_server else ''}",
                        value=auth_server,
                    )
                    for auth_server in auth_servers
                ],
                default=config.auth_manager.active_auth_server
                if config.auth_manager.active_auth_server in auth_servers
                else 0,
            ).execute_async()
            if not auth_server:
                console.info("Action cancelled.")
                sys.exit(1)

        if check_token:
            # Validate that the token is still valid by attempting to load it
            # Keep the original active server/auth server in case of failure
            previous_server = config.auth_manager.active_server
            previous_auth_server = config.auth_manager.active_auth_server

            config.auth_manager.active_server = server
            config.auth_manager.active_auth_server = auth_server

            try:
                token = await config.auth_manager.load_auth_token()
                if not token:
                    # No token available, need to log in
                    # Restore previous state until login completes
                    config.auth_manager.active_server = previous_server
                    config.auth_manager.active_auth_server = previous_auth_server
                    # Fall through to login flow below
                else:
                    console.success(f"Logged in to [cyan]{server}[/cyan].")
                    return
            except Exception as e:
                console.warning(f"Failed to load authentication token: {e!s}")
                # Token refresh failed due to invalid/expired refresh token or some other error (e.g. network issue) - in any case, we try to log in again
                log_in_message = "Please try to log in again."
                # Restore previous state until login completes
                config.auth_manager.active_server = previous_server
                config.auth_manager.active_auth_server = previous_auth_server
                # Fall through to login flow below

    # Starting the login flow
    console.info(log_in_message)

    try:
        oauth_metadata = await config.auth_manager.fetch_oauth_protected_resource_metadata(server)
    except RuntimeError as e:
        console.error(str(e))
        sys.exit(1)

    auth_servers = oauth_metadata.get("authorization_servers", [])
    auth_server = None
    token = None

    client_id = config.client_id
    client_secret = config.client_secret
    registration_token = None

    if auth_servers:
        if len(auth_servers) == 1:
            auth_server = auth_servers[0]
        else:
            auth_server = await inquirer.select(
                message="Select an authorization server:",
                choices=auth_servers,
            ).execute_async() or sys.exit(1)

        oidc = await config.auth_manager.get_oidc_metadata(auth_server)

        registration_endpoint = oidc["registration_endpoint"]
        if not client_id and registration_endpoint:
            async with httpx.AsyncClient() as client:
                resp = None
                try:
                    app_name = get_unique_app_name()
                    resp = await client.post(
                        registration_endpoint,
                        json={
                            "client_name": app_name,
                            "grant_types": ["authorization_code", "refresh_token"],
                            "enforce_pkce": True,
                            "all_users_entitled": True,
                            "redirect_uris": [REDIRECT_URI],
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    client_id = data["client_id"]
                    client_secret = data["client_secret"]
                    registration_token = data["registration_access_token"]
                except Exception as e:
                    if resp:
                        try:
                            error_details = resp.json()
                            console.warning(
                                f"error: {error_details['error']} error description: {error_details['error_description']}"
                            )

                        except Exception:
                            console.info("No parsable json response from registration endpoint.")
                    console.warning(f" Dynamic client registration failed. Proceed with manual input.  {e!s}")

        if not client_id:
            client_id = (
                await inquirer.text(
                    message="Enter Client ID:",
                    instruction=f"(Redirect URI: {REDIRECT_URI})",
                ).execute_async()
                or "agentstack-cli"
            )
            if not client_id:
                raise RuntimeError("Client ID is mandatory. Action cancelled.")
            client_secret = await inquirer.secret(message="Enter Client Secret (optional):").execute_async() or None

        code_verifier = generate_token(64)

        auth_url = f"{oidc['authorization_endpoint']}?{
            urlencode(
                {
                    'client_id': client_id,
                    'response_type': 'code',
                    'redirect_uri': REDIRECT_URI,
                    'scope': ' '.join(oauth_metadata.get('scopes_supported', ['openid', 'email', 'profile'])),
                    'code_challenge': typing.cast(str, create_s256_code_challenge(code_verifier)),
                    'code_challenge_method': 'S256',
                }
            )
        }"

        console.info(f"Opening browser for login: [cyan]{auth_url}[/cyan]")
        if not webbrowser.open(auth_url):
            console.warning("Could not open browser. Please visit the above URL manually.")

        code = await _wait_for_auth_code()
        async with httpx.AsyncClient() as client:
            token_resp = None
            try:
                token_resp = await client.post(
                    oidc["token_endpoint"],
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": REDIRECT_URI,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code_verifier": code_verifier,
                    },
                )
                token_resp.raise_for_status()
                token = token_resp.json()
            except Exception as e:
                if token_resp:
                    try:
                        error_details = token_resp.json()
                        console.warning(
                            f"error: {error_details['error']} error description: {error_details['error_description']}"
                        )
                    except Exception:
                        console.info("no parsable json response.")

                raise RuntimeError(f"Token request failed: {e}") from e

        if not token:
            raise RuntimeError("Login timed out or not successful.")

    config.auth_manager.save_auth_info(
        server=server,
        auth_server=auth_server,
        client_id=client_id,
        client_secret=client_secret,
        token=token,
        registration_token=registration_token,
    )

    config.auth_manager.active_server = server
    config.auth_manager.active_auth_server = auth_server
    console.success(f"Logged in to [cyan]{server}[/cyan].")


@app.command("logout | remove | rm | delete")
async def server_logout(
    all: typing.Annotated[
        bool,
        typer.Option(),
    ] = False,
):
    await config.auth_manager.cleanup_auth_session(all=all)
    console.success("You have been logged out.")


@app.command("show")
def server_show():
    if not config.auth_manager.active_server:
        console.info("No server selected.")
        console.hint(
            "Run [green]agentstack server list[/green] to list available servers, and [green]agentstack server login[/green] to select one."
        )
        return
    console.info(f"Active server: [cyan]{config.auth_manager.active_server}[/cyan]")


@app.command("list")
def server_list():
    if not config.auth_manager.servers:
        console.info("No servers found.")
        console.hint(
            "Run [green]agentstack platform start[/green] to start a local server, or [green]agentstack server login[/green] to connect to a remote one."
        )
        return
    for server in config.auth_manager.servers:
        console.print(
            f"[cyan]{server}[/cyan] {'[green](active)[/green]' if server == config.auth_manager.active_server else ''}"
        )
