# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os
import sys
import typing
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

from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.configuration import Configuration

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
                <p>You can safely close this tab and return to the BeeAI CLI.</p>
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


@app.command("login | change | select | default")
async def server_login(server: typing.Annotated[str | None, typer.Argument()] = None):
    """Login to a server or switch between logged in servers."""
    server = server or (
        await inquirer.select(  #  type: ignore
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
    server = server or await inquirer.text(message="Enter server URL:").execute_async()  #  type: ignore

    if server is None:
        raise RuntimeError("No server selected. Action cancelled.")

    if "://" not in server:
        server = f"https://{server}"

    server = server.rstrip("/")

    if server_data := config.auth_manager.get_server(server):
        console.info("Switching to an already logged in server.")
        auth_server = None
        auth_servers = list(server_data.authorization_servers.keys())
        if len(auth_servers) == 1:
            auth_server = auth_servers[0]
        elif len(auth_servers) > 1:
            auth_server = await inquirer.select(  #  type: ignore
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
    else:
        console.info("No authentication tokens found for this server. Proceeding to log in.")
        # use case where a developer is spinning up the platform using the Certificate manager's TLS certs.
        verify = os.environ.get("CLIENT_VERIFY_TLS", True)
        if verify == "False":
            verify = False
        async with httpx.AsyncClient(verify=verify) as client:
            resp = await client.get(f"{server}/.well-known/oauth-protected-resource/", follow_redirects=True)
            if resp.is_error:
                console.error("This server does not appear to run a compatible version of BeeAI Platform.")
                sys.exit(1)
            metadata = resp.json()

        auth_servers = metadata.get("authorization_servers", [])
        auth_server = None
        token = None
        if auth_servers:
            if len(auth_servers) == 1:
                auth_server = auth_servers[0]
            else:
                auth_server = await inquirer.select(  # type: ignore
                    message="Select an authorization server:",
                    choices=auth_servers,
                ).execute_async()

            if not auth_server:
                raise RuntimeError("No authorization server selected.")

            async with httpx.AsyncClient(verify=verify) as client:
                try:
                    resp = await client.get(f"{auth_server}/.well-known/openid-configuration")
                    resp.raise_for_status()
                    oidc = resp.json()
                except Exception as e:
                    raise RuntimeError(f"OIDC discovery failed: {e}") from e

            code_verifier = generate_token(64)

            auth_url = f"{oidc['authorization_endpoint']}?{
                urlencode(
                    {
                        'client_id': config.client_id,
                        'response_type': 'code',
                        'redirect_uri': REDIRECT_URI,
                        'scope': ' '.join(metadata.get('scopes_supported', ['openid'])),
                        'code_challenge': typing.cast(str, create_s256_code_challenge(code_verifier)),
                        'code_challenge_method': 'S256',
                    }
                )
            }"

            console.info(f"Opening browser for login: [cyan]{auth_url}[/cyan]")
            if not webbrowser.open(auth_url):
                console.warning("Could not open browser. Please visit the above URL manually.")

            code = await _wait_for_auth_code()
            console.info("got code [green]OK[/green].")
            post_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": config.client_id,
                "code_verifier": code_verifier,
            }
            # allow a developer to test using a client secret.
            # In production this is not necessary, however some provisioners do not
            # properly support authorization code with PKCE.
            # Further, the oidc configuration must be registerd with the platform
            # and in local mode in order to verify and validate access tokens.  The
            # associated production confugration is not available on local.
            client_secret = os.environ.get("CLIENT_SECRET", "")
            if client_secret is not None and client_secret != "":
                post_data["client_secret"] = client_secret
            async with httpx.AsyncClient() as client:
                token_resp = None
                try:
                    token_resp = await client.post(oidc["token_endpoint"], data=post_data)
                    token_resp.raise_for_status()
                    token = token_resp.json()
                except Exception as e:
                    console.error(f"token request error: {e!s}")
                    if token_resp is not None:
                        console.error(f"token_resp: {token_resp.json()!s}")
                    raise RuntimeError(f"Token request failed: {e}") from e

            if not token:
                raise RuntimeError("Login timed out or not successful.")

        config.auth_manager.save_auth_token(server, auth_server, token)

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
    config.auth_manager.clear_auth_token(all=all)
    console.success("You have been logged out.")


@app.command("show")
def server_show():
    if not config.auth_manager.active_server:
        console.info("No server selected.")
        console.hint(
            "Run [green]beeai server list[/green] to list available servers, and [green]beeai server login[/green] to select one."
        )
        return
    console.info(f"Active server: [cyan]{config.auth_manager.active_server}[/cyan]")


@app.command("list")
def server_list():
    if not config.auth_manager.servers:
        console.info("No servers found.")
        console.hint(
            "Run [green]beeai platform start[/green] to start a local server, or [green]beeai server login[/green] to connect to a remote one."
        )
        return
    for server in config.auth_manager.servers:
        console.print(
            f"[cyan]{server}[/cyan] {'[green](active)[/green]' if server == config.auth_manager.active_server else ''}"
        )
