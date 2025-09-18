# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import sys
import time
import typing
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import anyio
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


async def _get_server_metadata(server_url: str, ca_cert_file: Path):
    verify_option = await get_verify_option(server_url, ca_cert_file)
    async with httpx.AsyncClient(verify=verify_option) as client:
        resp = await client.get(f"{server_url}/api/v1/.well-known/oauth-protected-resource")
        if resp.is_error:
            console.error("This server does not appear to run a compatible version of BeeAI Platform.")
            sys.exit(1)
        return resp.json()


async def _discover_oidc_config(issuer: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{issuer}/.well-known/openid-configuration")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"OIDC discovery failed: {e}") from e


async def _wait_for_auth_code(port: int = 9001) -> str:
    result: dict = {}
    got_code = anyio.Event()
    app = FastAPI()

    @app.get("/callback")
    async def callback(request: Request):
        query = dict(request.query_params)
        result.update(query)
        got_code.set()
        html_content = """
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
            <p>You can safely close this tab and return to the CLI.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)

    server = uvicorn.Server(config=uvicorn.Config(app, host="127.0.0.1", port=9001, log_level=logging.ERROR))

    async with anyio.create_task_group() as tg:
        tg.start_soon(server.serve)
        await got_code.wait()
        server.should_exit = True

    return result["code"]


async def exchange_token(oidc: dict, code: str, code_verifier: str, config) -> dict:
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
            return token_resp.json()
        except Exception as e:
            raise RuntimeError(f"Token request failed: {e}") from e


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
        metadata = await _get_server_metadata(server_url=server, ca_cert_file=ca_cert_file)
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

        oidc = await _discover_oidc_config(auth_server)
        code_verifier = generate_token(64)

        auth_url = f"{oidc['authorization_endpoint']}?{
            urlencode(
                {
                    'client_id': config.client_id,
                    'response_type': 'code',
                    'redirect_uri': config.redirect_uri,
                    'scope': ' '.join(metadata.get('scopes_supported', ['openid'])),
                    'code_challenge': create_s256_code_challenge(code_verifier),
                    'code_challenge_method': 'S256',
                }
            )
        }"

        console.print()
        console.info(f"Opening browser for login: [cyan]{auth_url}[/cyan]")
        if not webbrowser.open(auth_url):
            console.warning("Could not open browser. Please visit the above URL manually.")

        code = await _wait_for_auth_code()
        token = await exchange_token(oidc, code, code_verifier, config)

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

    if config.server_metadata_dir.exists():
        for metadata_file in config.server_metadata_dir.glob("*_metadata.json"):
            try:
                if json.loads(metadata_file.read_text()).get("expiry", 0) <= time.time():
                    metadata_file.unlink()
            except Exception:
                metadata_file.unlink()

    console.print()
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
