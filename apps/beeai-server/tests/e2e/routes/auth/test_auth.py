# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from beeai_server.api.routes import auth
from beeai_server.configuration import Configuration
from beeai_server.service_layer.services.auth import AuthService


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_display_passcode():
    """test the display_passcoded method"""
    wow = MagicMock()
    auth_service = AuthService(wow, Configuration())
    response = await auth.display_passcode(auth_service, "123456")
    assert isinstance(response, HTMLResponse)
    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_token_by_passcode():
    """test the get_token method of the auth api route"""
    wow = MagicMock()
    auth_service = AuthService(wow, Configuration())
    response = await auth.get_token(auth_service, "dev")
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_login():
    """test the get_token method of the auth api route"""
    wow = MagicMock()
    auth_service = AuthService(wow, Configuration())
    request = MagicMock()
    response = await auth.login(auth_service, request, "https://beeai-platform.api.testing:8336")
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_auth_callback():
    """test the get_token method of the auth api route"""
    wow = MagicMock()
    auth_service = AuthService(wow, Configuration())
    request = MagicMock()
    with pytest.raises(Exception) as exc:
        await auth.auth_callback(request, Configuration(), auth_service)
        assert isinstance(exc, HTTPException)
