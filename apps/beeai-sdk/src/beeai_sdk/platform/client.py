# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import ssl
import typing

import httpx
from httpx import URL, AsyncBaseTransport
from httpx._client import EventHook
from httpx._config import DEFAULT_LIMITS, DEFAULT_MAX_REDIRECTS, DEFAULT_TIMEOUT_CONFIG, Limits
from httpx._types import AuthTypes, CertTypes, CookieTypes, HeaderTypes, ProxyTypes, QueryParamTypes, TimeoutTypes
from pydantic import Secret

from beeai_sdk.util import resource_context


class PlatformClient(httpx.AsyncClient):
    context_id: str | None = None

    def __init__(
        self,
        context_id: str | None = None,  # Enter context scope
        auth_token: str | Secret | None = None,
        *,
        auth: AuthTypes | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        verify: ssl.SSLContext | str | bool = True,
        cert: CertTypes | None = None,
        http1: bool = True,
        http2: bool = False,
        proxy: ProxyTypes | None = None,
        mounts: None | (typing.Mapping[str, AsyncBaseTransport | None]) = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
        follow_redirects: bool = False,
        limits: Limits = DEFAULT_LIMITS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        event_hooks: None | (typing.Mapping[str, list[EventHook]]) = None,
        base_url: URL | str = "",
        transport: AsyncBaseTransport | None = None,
        trust_env: bool = True,
        default_encoding: str | typing.Callable[[bytes], str] = "utf-8",
    ) -> None:
        if not base_url:
            base_url = os.environ.get("PLATFORM_URL", "http://127.0.0.1:8333")
        super().__init__(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            proxy=proxy,
            mounts=mounts,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks,
            base_url=base_url,
            transport=transport,
            trust_env=trust_env,
            default_encoding=default_encoding,
        )
        self.context_id = context_id
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"


get_platform_client, use_platform_client = resource_context(factory=PlatformClient, default_factory=PlatformClient)

__all__ = ["PlatformClient", "get_platform_client", "use_platform_client"]
