# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import anyio
import httpx
import uvicorn
from authlib.common.security import generate_token
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from InquirerPy import inquirer

from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.configuration import Configuration
from beeai_cli.utils import get_server_ca_cert, get_verify_option, make_safe_name, normalize_url

app = AsyncTyper()

config = Configuration()


async def get_server_metadata(server_url: str, ca_cert_file: Path, force_refresh=False):
    safe_name = make_safe_name(server_url)
    metadata_file = config.server_metadata_dir / f"{safe_name}_metadata.json"

    if not force_refresh and metadata_file.exists():
        data = json.loads(metadata_file.read_text())
        if data.get("expiry", 0) > time.time():
            return data["metadata"]

    verify_option = await get_verify_option(server_url, ca_cert_file)
    async with httpx.AsyncClient(verify=verify_option) as client:
        resp = await client.get(f"{server_url}/api/v1/.well-known/oauth-protected-resource")
        resp.raise_for_status()
        metadata = resp.json()

    payload = {"metadata": metadata, "expiry": time.time() + config.server_metadata_ttl}
    metadata_file.write_text(json.dumps(payload, indent=2))
    return metadata


async def discover_oidc_config(issuer: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{issuer}/.well-known/openid-configuration")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"OIDC discovery failed: {e}") from e


async def wait_for_auth_code(port: int = 9001) -> str:
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

    server = uvicorn.Server(config=uvicorn.Config(app, host="127.0.0.1", port=9001, log_level="error"))

    async with anyio.create_task_group() as tg:
        tg.start_soon(server.serve)
        await got_code.wait()
        server.should_exit = True

    return result["code"]


async def exchange_token(oidc: dict, code: str, code_verifier: str, config) -> dict:
    token_req = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.redirect_uri,
        "client_id": config.client_id,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient() as client:
        try:
            token_resp = await client.post(oidc["token_endpoint"], data=token_req)
            token_resp.raise_for_status()
            return token_resp.json()
        except Exception as e:
            raise RuntimeError(f"Token request failed: {e}") from e


@app.command("login")
async def login(server_url: str | None = None):
    default_url = config.auth_manager.get_active_server()
    if not default_url:
        default_url = config.default_external_host
    if not server_url:
        server_url = await inquirer.text(  # type: ignore
            message=f"🌐 Enter the server address (default: {default_url}):",
            default=str(default_url),
            validate=lambda val: bool(val.strip()),
        ).execute_async()
    if server_url is None:
        raise RuntimeError("No server URL provided.")

    server_url = normalize_url(server_url)

    ca_cert_file = await get_server_ca_cert(
        server_url=server_url, ca_cert_file=config.ca_cert_dir / f"{make_safe_name(server_url)}_ca.crt"
    )
    metadata = await get_server_metadata(server_url=server_url, ca_cert_file=ca_cert_file)
    auth_servers = metadata.get("authorization_servers", [])

    if not auth_servers:
        console.print()
        console.error("No authorization servers found.")
        raise RuntimeError("Login failed due to missing authorization servers.")

    if len(auth_servers) == 1:
        issuer = auth_servers[0]
        if not isinstance(issuer, str):
            raise RuntimeError("Invalid authorization server format.")
    else:
        console.print("\n[bold blue]Multiple authorization servers are available.[/bold blue]")
        issuer = await inquirer.select(  # type: ignore
            message="Select an authorization server:",
            choices=auth_servers,
            default=auth_servers[0],
            pointer="👉",
        ).execute_async()

    if not issuer:
        raise RuntimeError("No issuer selected.")

    oidc = await discover_oidc_config(issuer)
    code_verifier = generate_token(64)
    code_challenge = create_s256_code_challenge(code_verifier)

    requested_scopes = metadata.get("scopes_supported", [])
    if not requested_scopes:
        requested_scopes = ["openid"]  # default fallback

    auth_params = {
        "client_id": config.client_id,
        "response_type": "code",
        "redirect_uri": config.redirect_uri,
        "scope": " ".join(requested_scopes),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{oidc['authorization_endpoint']}?{urlencode(auth_params)}"

    console.print(f"\n[bold blue]Opening browser for login:[/bold blue] [cyan]{auth_url}[/cyan]")
    webbrowser.open(auth_url)

    code = await wait_for_auth_code()
    tokens = await exchange_token(oidc, code, code_verifier, config)

    if tokens:
        config.auth_manager.save_auth_token(make_safe_name(server_url), issuer, tokens)
        console.print()
        console.success("Login successful.")
        return

    console.print()
    console.error("Login timed out or not successful.")
    raise RuntimeError("Login failed.")


@app.command("logout")
async def logout():
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
def show_server():
    active_server = config.auth_manager.get_active_server()
    if not active_server:
        console.print("[bold red]No active server!!![/bold red]\n")
        return
    console.print(f"\n[bold]Active server:[/bold] [green]{active_server}[/green]\n")


@app.command("list")
def list_server():
    servers = config.auth_manager.config.get("servers", {})
    if not servers:
        console.print("[bold red]No servers logged in.[/bold red]\nRun [bold green]beeai login[/bold green] first.\n")
        return
    console.print("\n[bold blue]Known servers:[/bold blue]")
    for i, server in enumerate(servers, start=1):
        marker = " [green]✅(active)[/green]" if server == config.auth_manager.get_active_server() else ""
        console.print(f"[cyan]{i}. {server}[/cyan] {marker}")


@app.command("change | select | default")
def switch_server():
    servers = config.auth_manager.config.get("servers", {})
    if not servers:
        console.print("[bold red]No server logged in.[/bold red] Run [bold green]beeai login[/bold green] first.\n")

    console.print("\n[bold blue]Available servers:[/bold blue]")
    choices = [
        {
            "name": f"{i + 1}. {server} {' ✅(active)' if server == config.auth_manager.get_active_server() else ''}",
            "value": server,
        }
        for i, server in enumerate(servers)
    ]

    selected_server = inquirer.select(  # type: ignore
        message="Select a server:",
        choices=choices,
        default=config.auth_manager.get_active_server() if config.auth_manager.get_active_server() else None,
        pointer="👉",
    ).execute()

    server_data = servers[selected_server]
    auth_servers = list(server_data.get("authorization_servers", {}).keys())

    if not auth_servers:
        console.print(
            f"[bold red]No tokens available for [cyan]{selected_server}[/cyan].[/bold red] You may need to run [green]beeai login -- {selected_server}[/green]."
        )
        return
    if len(auth_servers) == 1:
        selected_issuer = auth_servers[0]
    else:
        console.print("[bold blue]Multiple authorization servers are available.[/bold blue]")
        auth_server_choices = [
            {
                "name": f"{j + 1}. {issuer} {' ✅(active)' if selected_server == config.auth_manager.config.get('active_server') and issuer == config.auth_manager.config.get('active_token') else ''}",
                "value": issuer,
            }
            for j, issuer in enumerate(auth_servers)
        ]
        selected_issuer = inquirer.select(  # type: ignore
            message="Select an authorization server:",
            choices=auth_server_choices,
            pointer="👉",
        ).execute()

    config.auth_manager.set_active_server(selected_server)
    config.auth_manager.set_active_token(selected_server, selected_issuer)

    console.print(f"\n[bold green]Switched to:[/bold green] [cyan]{selected_server}[/cyan]")
