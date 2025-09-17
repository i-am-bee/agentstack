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
from beeai_cli.utils import get_resource_ca_cert, get_verify_option, make_safe_name, normalize_url

app = AsyncTyper()

config = Configuration()


async def get_resource_metadata(resource_url: str, ca_cert_file: Path, force_refresh=False):
    safe_name = make_safe_name(resource_url)
    metadata_file = config.resource_metadata_dir / f"{safe_name}_metadata.json"

    if not force_refresh and metadata_file.exists():
        data = json.loads(metadata_file.read_text())
        if data.get("expiry", 0) > time.time():
            return data["metadata"]

    url = f"{resource_url}/api/v1/.well-known/oauth-protected-resource"
    verify_option = await get_verify_option(resource_url, ca_cert_file)
    async with httpx.AsyncClient(verify=verify_option) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        metadata = resp.json()

    payload = {"metadata": metadata, "expiry": time.time() + config.resource_metadata_ttl}
    metadata_file.write_text(json.dumps(payload, indent=2))
    return metadata


def generate_pkce_pair():
    code_verifier = generate_token(64)
    code_challenge = create_s256_code_challenge(code_verifier)
    return code_verifier, code_challenge


async def discover_oidc_config(issuer: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{issuer}/.well-known/openid-configuration")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"OIDC discovery failed: {e}") from e


def make_callback_app(result: dict, got_code: anyio.Event) -> FastAPI:
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

    return app


async def wait_for_auth_code(port: int = 9001) -> str:
    result: dict = {}
    got_code = anyio.Event()
    app = make_callback_app(result, got_code)

    server_config = uvicorn.Config(app, host="127.0.0.1", port=9001, log_level="error")
    server = uvicorn.Server(config=server_config)

    async def run_server():
        await server.serve()

    async with anyio.create_task_group() as tg:
        tg.start_soon(run_server)
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
async def cli_login(resource_url: str | None = None):
    default_url = config.auth_manager.get_active_resource()
    if not default_url:
        default_url = config.default_external_host
    if not resource_url:
        resource_url = await inquirer.text(  # type: ignore
            message=f"🌐 Enter the server address (default: {default_url}):",
            default=str(default_url),
            validate=lambda val: bool(val.strip()),
        ).execute_async()
    if resource_url is None:
        raise RuntimeError("No resource URL provided.")

    resource_url = normalize_url(resource_url)

    ca_cert_file = await get_resource_ca_cert(
        resource_url=resource_url, ca_cert_file=config.ca_cert_dir / f"{make_safe_name(resource_url)}_ca.crt"
    )
    metadata = await get_resource_metadata(resource_url=resource_url, ca_cert_file=ca_cert_file)
    auth_servers = metadata.get("authorization_servers", [])

    if not auth_servers:
        console.print()
        console.error("No authorization servers found for this resource.")
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
    code_verifier, code_challenge = generate_pkce_pair()

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
        config.auth_manager.save_auth_token(make_safe_name(resource_url), issuer, tokens)
        console.print()
        console.success("Login successful.")
        return

    console.print()
    console.error("Login timed out or not successful.")
    raise RuntimeError("Login failed.")


@app.command("logout")
async def logout():
    config.auth_manager.clear_auth_token()

    if config.resource_metadata_dir.exists():
        for metadata_file in config.resource_metadata_dir.glob("*_metadata.json"):
            try:
                if json.loads(metadata_file.read_text()).get("expiry", 0) <= time.time():
                    metadata_file.unlink()
            except Exception:
                metadata_file.unlink()

    console.print()
    console.success("You have been logged out.")


@app.command("show")
def show_server():
    active_resource = config.auth_manager.get_active_resource()
    if not active_resource:
        console.print("[bold red]No active server!!![/bold red]\n")
        return
    console.print(f"\n[bold]Active server:[/bold] [green]{active_resource}[/green]\n")


@app.command("list")
def list_server():
    resources = config.auth_manager.config.get("resources", {})
    if not resources:
        console.print("[bold red]No servers logged in.[/bold red]\nRun [bold green]`beeai login`[/bold green] first.\n")
        return
    console.print("\n[bold blue]Known servers:[/bold blue]")
    for i, res in enumerate(resources, start=1):
        marker = " [green]✅(active)[/green]" if res == config.auth_manager.get_active_resource() else ""
        console.print(f"[cyan]{i}. {res}[/cyan] {marker}")


@app.command("change | select | default")
def switch_server():
    resources = config.auth_manager.config.get("resources", {})
    if not resources:
        console.print("[bold red]No server logged in.[/bold red] Run [bold green]`beeai login`[/bold green] first.\n")

    console.print("\n[bold blue]Available servers:[/bold blue]")
    choices = [
        {
            "name": f"{i + 1}. {res} {' ✅(active)' if res == config.auth_manager.get_active_resource() else ''}",
            "value": res,
        }
        for i, res in enumerate(resources)
    ]

    selected_resource = inquirer.select(  # type: ignore
        message="Select a server:",
        choices=choices,
        default=config.auth_manager.get_active_resource() if config.auth_manager.get_active_resource() else None,
        pointer="👉",
    ).execute()

    resource_data = resources[selected_resource]
    auth_servers = list(resource_data.get("authorization_servers", {}).keys())

    if not auth_servers:
        console.print(
            f"[bold red]No tokens available for [cyan]{selected_resource}[/cyan].[/bold red] You may need to run [bolc green]`beeai login -- {selected_resource}`[/bold green]."
        )
        return
    if len(auth_servers) == 1:
        selected_issuer = auth_servers[0]
    else:
        console.print("[bold blue]Multiple authorization servers are available.[/bold blue]")
        auth_server_choices = [
            {
                "name": f"{j + 1}. {issuer} {' ✅(active)' if selected_resource == config.auth_manager.config.get('active_resource') and issuer == config.auth_manager.config.get('active_token') else ''}",
                "value": issuer,
            }
            for j, issuer in enumerate(auth_servers)
        ]
        selected_issuer = inquirer.select(  # type: ignore
            message="Select an authorization server:",
            choices=auth_server_choices,
            pointer="👉",
        ).execute()

    config.auth_manager.set_active_resource(selected_resource)
    config.auth_manager.set_active_token(selected_resource, selected_issuer)

    console.print(f"\n[bold green]Switched to:[/bold green] [cyan]{selected_resource}[/cyan]")
