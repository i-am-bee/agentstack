# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import secrets
import string

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)

SLASH_LOGIN = "/login"


@inject
class AuthService:
    def __init__(self, uow: IUnitOfWorkFactory, configuration: Configuration):
        self._uow = uow
        self._config = configuration
        self._oauth = self._build_oauth()

    def _build_oauth(self) -> OAuth | None:
        if self._config.oidc.disable_oidc:
            return None
        issuer = str(self._config.oidc.issuer)
        oauth = OAuth()
        oauth.register(
            name="auth_provider",
            client_id=self._config.oidc.client_id,
            client_secret=self._config.oidc.client_secret._secret_value,
            server_metadata_url=f"{issuer}/.well-known/openid-configuration",
            jwks_url=str(self._config.oidc.jwks_url),
            client_kwargs={"scope": "openid email profile"},
        )
        return oauth

    async def login(self, request: Request, callback_url: str) -> JSONResponse | RedirectResponse:
        if self._oauth is None:
            return JSONResponse({"login_url": None, "passcode": "dev", "token": "beeai-dev-token"})

        redirect_uri = str(request.url_for("auth_callback"))

        request.session["callback_url"] = callback_url
        request.session["redirect_uri"] = redirect_uri

        response = await self._oauth.auth_provider.authorize_redirect(request, redirect_uri)

        # Redirect the user to the authorization URL of the IDP
        idp_authorization_url = response.headers.get("location")
        logger.info(f"Redirecting to IDP login page: {idp_authorization_url}")

        return RedirectResponse(idp_authorization_url)

    async def handle_callback(self, request: Request, pending_tokens: dict[str, dict]):
        if self._oauth is None:
            raise HTTPException(status_code=503, detail="OIDC disabled in configuration")

        callback_url = request.session.get("callback_url")
        if not callback_url:
            logger.error("Callback URL is NULL.")
            return RedirectResponse(SLASH_LOGIN)

        passcode = "".join(secrets.choice(string.ascii_letters) for _ in range(10))

        try:
            token = await self._oauth.auth_provider.authorize_access_token(request)
        except Exception as e:
            logger.debug("Error running authorize_access_token %s", str(e))
            return RedirectResponse(SLASH_LOGIN)

        if passcode and token:
            async with self._uow() as uow:
                await uow.tokens.set(passcode, token)
                await uow.commit()

        delimiter = "&" if "?" in callback_url else "?"
        callback_url += f"{delimiter}passcode={passcode}"

        return RedirectResponse(callback_url)

    async def render_display_passcode_page(self, passcode: str) -> HTMLResponse:
        display_passcode = passcode or "Not Available"
        expiry_seconds = self._config.oidc.passcode_ttl_seconds  # 5 minutes

        return HTMLResponse(f"""
        <html>
            <head>
                <title>One-Time Passcode</title>
                <style>
                    body {{
                        font-family: sans-serif;
                        padding: 2rem;
                    }}
                    .passcode-container {{
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }}
                    .copy-icon {{
                        cursor: pointer;
                        font-size: 1.2rem;
                        padding: 0.3rem 0.6rem;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background-color: #f5f5f5;
                        transition: background-color 0.2s ease;
                    }}
                    .copy-icon:hover {{
                        background-color: #e0e0e0;
                    }}
                    .expired {{
                        color: red;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <h3>You are logging in with W3ID</h3>
                <div class="passcode-container" id="passcode-section">
                    <strong>Your one-time passcode is:</strong>
                    <span id="passcode">{display_passcode}</span>
                    <span class="copy-icon" onclick="copyPasscode()" id="copy-btn">📋</span>
                </div>
                <div id="timer" style="margin-top: 0.5rem;"></div>
                <div id="expiry-message" class="expired" style="display:none;">
                    Expired
                </div>

                <script>
                    const expirySeconds = {expiry_seconds};
                    let remaining = expirySeconds;

                    const timerEl = document.getElementById('timer');
                    const passcodeEl = document.getElementById('passcode');
                    const expiryMessageEl = document.getElementById('expiry-message');
                    const copyBtnEl = document.getElementById('copy-btn');

                    function formatTime(seconds) {{
                        const minutes = Math.floor(seconds / 60);
                        const secs = seconds % 60;
                        return `${{minutes}}:${{secs.toString().padStart(2, '0')}}`;
                    }}

                    function updateTimer() {{
                        if (remaining > 0) {{
                            timerEl.textContent = "It will expire in " + formatTime(remaining) + " minutes.";
                            remaining--;
                        }} else {{
                            clearInterval(timerInterval);
                            passcodeEl.textContent = '';
                            copyBtnEl.style.display = 'none';
                            timerEl.style.display = 'none';
                            expiryMessageEl.style.display = 'block';
                        }}
                    }}

                    const timerInterval = setInterval(updateTimer, 1000);
                    updateTimer();

                    function copyPasscode() {{
                        const passcodeText = passcodeEl.innerText;
                        if (!passcodeText) return;
                        navigator.clipboard.writeText(passcodeText).catch(function(err) {{
                            console.log("Failed to copy passcode:", err);
                        }});
                    }}
                </script>
            </body>
        </html>
        """)

    async def get_token_by_passcode(self, passcode: str, pending_tokens: dict) -> JSONResponse:
        if passcode == "dev":
            return JSONResponse(status_code=200, content={"token": "beeai-dev-token"})
        async with self._uow() as uow:
            token = await uow.tokens.get(passcode)
        if token:
            return JSONResponse(status_code=200, content={"token": token})
        raise HTTPException(status_code=404, detail="Token not found or expired")
