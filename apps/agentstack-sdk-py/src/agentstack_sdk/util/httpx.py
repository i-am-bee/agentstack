# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


import httpx


class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

    async def async_auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request
