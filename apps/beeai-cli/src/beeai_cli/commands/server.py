# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
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
from beeai_cli.utils import get_server_ca_cert, get_verify_option, make_safe_name

app = AsyncTyper()

config = Configuration()


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


@app.command("login")
async def server_login(server: typing.Annotated[str | None, typer.Argument()] = None):
    """Login to a server or switch between logged in servers."""
    servers = config.auth_manager.config.get("servers", {})
    active_server = config.auth_manager.get_active_server()
    server = server or (
        await inquirer.select(  #  type: ignore
            message="Select a server to activate, or log in to a new one:",
            choices=[
                *(Choice(name=f"{s} {'(active)' if s == active_server else ''}", value=s) for s in servers),
                Choice(name="Log in to a new server", value=None),
            ],
            default=0,
        ).execute_async()
        if servers
        else None
    )
    server = server or await inquirer.text(message="Enter server URL:").execute_async()  #  type: ignore

    if server is None:
        raise RuntimeError("No server selected. Action cancelled.")

    if "://" not in server:
        server = f"https://{server}"

    server = server.rstrip("/")

    servers = config.auth_manager.config.get("servers", {})
    server_data = servers.get(server, {})
    auth_servers = list(server_data.get("authorization_servers", {}).keys())

    if auth_servers:
        console.info("Switching to already logged in server.")
        auth_server = None
        if len(auth_servers) == 1:
            auth_server = auth_servers[0]
        else:
            active_token_issuer = None
            if server == config.auth_manager.get_active_server():
                active_token_issuer = config.auth_manager.config.get("active_token")

            auth_server = await inquirer.select(  #  type: ignore
                message="Select an authorization server:",
                choices=[
                    Choice(name=f"{issuer} {'(active)' if issuer == active_token_issuer else ''}", value=issuer)
                    for issuer in auth_servers
                ],
                default=active_token_issuer,
            ).execute_async()

        if not auth_server:
            console.info("Action cancelled.")
            return
    else:
        console.info("No authentication tokens found for this server. Proceeding to log in.")
        ca_cert_file = await get_server_ca_cert(
            server_url=server, ca_cert_file=config.ca_cert_dir / f"{make_safe_name(server)}_ca.crt"
        )
        verify_option = await get_verify_option(server, ca_cert_file)
        async with httpx.AsyncClient(verify=verify_option) as client:
            resp = await client.get(f"{server}/api/v1/.well-known/oauth-protected-resource")
            if resp.is_error:
                console.error("This server does not appear to run a compatible version of BeeAI Platform.")
                sys.exit(1)
            metadata = resp.json()
        auth_servers = metadata.get("authorization_servers", [])

        if not auth_servers:
            raise RuntimeError("No authorization servers found.")

        auth_server = None
        if len(auth_servers) == 1:
            auth_server = auth_servers[0]
        else:
            auth_server = await inquirer.select(  # type: ignore
                message="Select an authorization server:",
                choices=auth_servers,
            ).execute_async()

        if not auth_server:
            raise RuntimeError("No authorization server selected.")

        async with httpx.AsyncClient() as client:
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
                    'redirect_uri': config.redirect_uri,
                    'scope': ' '.join(metadata.get('scopes_supported', ['openid'])),
                    'code_challenge': typing.cast(str, create_s256_code_challenge(code_verifier)),
                    'code_challenge_method': 'S256',
                }
            )
        }"

        console.print()
        console.info(f"Opening browser for login: [cyan]{auth_url}[/cyan]")
        if not webbrowser.open(auth_url):
            console.warning("Could not open browser. Please visit the above URL manually.")

        code = await _wait_for_auth_code()
        async with httpx.AsyncClient() as client:
            try:
                token_resp = await client.post(
                    oidc["token_endpoint"],
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": config.redirect_uri,
                        "client_id": config.client_id,
                        "code_verifier": code_verifier,
                    },
                )
                token_resp.raise_for_status()
                token = token_resp.json()
            except Exception as e:
                raise RuntimeError(f"Token request failed: {e}") from e

        if not token:
            raise RuntimeError("Login timed out or not successful.")

        config.auth_manager.save_auth_token(server, auth_server, token)

    config.auth_manager.set_active_server(server)
    config.auth_manager.set_active_token(server, auth_server)
    console.print()
    console.success(f"Logged in to [cyan]{server}[/cyan].")


@app.command("logout")
async def server_logout():
    config.auth_manager.clear_auth_token()
    console.success("You have been logged out.")


@app.command("show")
def server_show():
    active_server = config.auth_manager.get_active_server()
    if not active_server:
        console.info("No active server.")
        return
    console.info(f"Active server: [cyan]{active_server}[/cyan]")


@app.command("list")
def server_list():
    servers = config.auth_manager.config.get("servers", {})
    if not servers:
        console.info("No servers logged in.")
        console.hint("Run [green]beeai login[/green] to log in.")
        return
    for server in servers:
        console.print(
            f"[cyan]{server}[/cyan] {'[green](active)[/green]' if server == config.auth_manager.get_active_server() else ''}"
        )
