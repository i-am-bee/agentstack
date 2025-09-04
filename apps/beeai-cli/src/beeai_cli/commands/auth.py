# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import json
import time
import webbrowser
from urllib.parse import urlencode

import anyio
import httpx
import uvicorn
from authlib.common.security import generate_token
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.configuration import Configuration
from beeai_cli.utils import make_safe_name

app = AsyncTyper()

config = Configuration()


async def get_resource_metadata(resource_url: str, force_refresh=False):
    safe_name = make_safe_name(resource_url)
    metadata_file = config.resource_metadata_dir / f"{safe_name}_metadata.json"

    if not force_refresh and metadata_file.exists():
        data = json.loads(metadata_file.read_text())
        if data.get("expiry", 0) > time.time():
            return data["metadata"]

    url = f"{resource_url}api/v1/.well-known/oauth-protected-resource"
    async with httpx.AsyncClient() as client:
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
    if not resource_url:
        entered = input(f"Enter the server url (default: {config.host}):").strip()
        resource_url = entered or str(config.host)

    metadata = await get_resource_metadata(resource_url=resource_url)
    auth_servers = metadata.get("authorization_servers", [])

    if not auth_servers:
        console.print("[bold red]No authorization servers found for this resource.[/bold red]")
        raise RuntimeError("Login failed due to missing authorization servers.")

    if len(auth_servers) == 1:
        issuer = auth_servers[0]
    else:
        console.print("Multiple authorization servers are available.\n")
        for i, as_url in enumerate(auth_servers, start=1):
            console.print(f"{i}. {as_url}")
        choice = input("\nSelect an authorization server: ").strip()
        if not choice:
            choice = "1"
        try:
            idx = int(choice) - 1
            issuer = auth_servers[idx]
        except (ValueError, IndexError):
            raise ValueError("Invalid choice") from None

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

    console.print(f"\nOpening browser for login: {auth_url}")
    webbrowser.open(auth_url)

    code = await wait_for_auth_code()
    tokens = await exchange_token(oidc, code, code_verifier, config)

    if tokens:
        config.auth_manager.save_auth_token(resource_url, issuer, tokens)
        console.print("\n[bold green]Ok! Login successful.[/bold green]")
        return

    console.print("\n [bold red] Login timed out or not successful. [/bold red] ")
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

    console.print("\n[bold yellow]You have been logged out.[/bold yellow]")
