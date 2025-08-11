# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging

from fastapi import APIRouter, Query, Request

from beeai_server.api.dependencies import AuthServiceDependency, ConfigurationDependency

logger = logging.getLogger(__name__)

SLASH_LOGIN = "/login"

router = APIRouter()

pending_tokens: dict[str, dict] = {}


@router.get("/login")
async def login(
    auth_service: AuthServiceDependency,
    request: Request,
    callback_url: str = Query(
        ..., description="The URL to which the actor will be redirected after completing the login process."
    ),
):
    if not (callback_url.startswith("http://") or callback_url.startswith("https://")):
        callback_url = "https://" + callback_url  # Default to HTTPS; adjust as needed
    return await auth_service.login(request=request, callback_url=callback_url)


@router.get("/auth/callback")
async def auth_callback(request: Request, configuration: ConfigurationDependency, auth_service: AuthServiceDependency):
    return await auth_service.handle_callback(request, pending_tokens)


@router.get("/display-passcode")
async def display_passcode(auth_service: AuthServiceDependency, passcode: str = Query(None)):
    return await auth_service.render_display_passcode_page(passcode)


@router.get("/token")
async def get_token(auth_service: AuthServiceDependency, passcode: str = Query(None)):
    return await auth_service.get_token_by_passcode(passcode, pending_tokens)
