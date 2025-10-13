# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ipaddress

from fastapi import status
from fastapi.staticfiles import StaticFiles
from starlette.responses import AsyncContentStream, StreamingResponse
from uvicorn._types import ASGI3Application, ASGIReceiveCallable, ASGISendCallable, Scope

from beeai_server.api.schema.common import ErrorStreamResponse, ErrorStreamResponseError
from beeai_server.utils.utils import extract_messages


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


def encode_stream(chunk: str) -> str:
    return f"data: {chunk}\n\n"


def streaming_response(content: AsyncContentStream):
    async def wrapper(stream):
        try:
            async for chunk in stream:
                yield encode_stream(chunk)
        except Exception as ex:
            errors = extract_messages(ex)
            if len(errors) == 1:
                [(error, message)] = errors
            else:
                error = "ExceptionGroup"
                message = repr(errors)
            yield encode_stream(
                ErrorStreamResponse(
                    error=ErrorStreamResponseError(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, type=error, detail=message
                    )
                ).model_dump_json()
            )

    return StreamingResponse(
        wrapper(content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


class ProxyHeadersMiddleware:
    """
    Modified https://github.com/Kludex/uvicorn/blob/main/uvicorn/middleware/proxy_headers.py
    Removed "for"
    Added "host" support
    """

    def __init__(self, app: ASGI3Application, trusted_hosts: list[str] | str = "127.0.0.1") -> None:
        self.app = app
        self.trusted_hosts = _TrustedHosts(trusted_hosts)

    async def __call__(self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)

        client_addr = scope.get("client")
        client_host = client_addr[0] if client_addr else None

        if client_host in self.trusted_hosts:
            headers = dict(scope["headers"])

            proto = None
            if b"x-forwarded-proto" in headers:
                proto = headers[b"x-forwarded-proto"].decode("latin1").strip()

            host = None
            if b"x-forwarded-host" in headers:
                host = headers[b"x-forwarded-host"].decode("latin1").strip()

            if b"forwarded" in headers:
                for forwarded in headers[b"forwarded"].decode("latin1").split(","):
                    directives = dict([(val.strip() for val in seg.split("=")) for seg in forwarded.split(";")])
                    if "proto" in directives or "host" in directives:
                        proto = directives.get("proto")
                        host = directives.get("host")
                        break

            if proto in {"http", "https", "ws", "wss"}:
                if scope["type"] == "websocket":
                    scope["scheme"] = proto.replace("http", "ws")
                else:
                    scope["scheme"] = proto

            if host:
                scope["headers"] = [
                    (key, value) if key != b"host" else (b"host", host.encode()) for key, value in scope["headers"]
                ]
                scope["server"] = (host, None)

        return await self.app(scope, receive, send)


def _parse_raw_hosts(value: str) -> list[str]:
    return [item.strip() for item in value.split(",")]


class _TrustedHosts:
    """Container for trusted hosts and networks"""

    def __init__(self, trusted_hosts: list[str] | str) -> None:
        self.always_trust: bool = trusted_hosts in ("*", ["*"])

        self.trusted_literals: set[str] = set()
        self.trusted_hosts: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
        self.trusted_networks: set[ipaddress.IPv4Network | ipaddress.IPv6Network] = set()

        # Notes:
        # - We separate hosts from literals as there are many ways to write
        #   an IPv6 Address so we need to compare by object.
        # - We don't convert IP Address to single host networks (e.g. /32 / 128) as
        #   it more efficient to do an address lookup in a set than check for
        #   membership in each network.
        # - We still allow literals as it might be possible that we receive a
        #   something that isn't an IP Address e.g. a unix socket.

        if not self.always_trust:
            if isinstance(trusted_hosts, str):
                trusted_hosts = _parse_raw_hosts(trusted_hosts)

            for host in trusted_hosts:
                # Note: because we always convert invalid IP types to literals it
                # is not possible for the user to know they provided a malformed IP
                # type - this may lead to unexpected / difficult to debug behaviour.

                if "/" in host:
                    # Looks like a network
                    try:
                        self.trusted_networks.add(ipaddress.ip_network(host))
                    except ValueError:
                        # Was not a valid IP Network
                        self.trusted_literals.add(host)
                else:
                    try:
                        self.trusted_hosts.add(ipaddress.ip_address(host))
                    except ValueError:
                        # Was not a valid IP Address
                        self.trusted_literals.add(host)

    def __contains__(self, host: str | None) -> bool:
        if self.always_trust:
            return True

        if not host:
            return False

        try:
            ip = ipaddress.ip_address(host)
            if ip in self.trusted_hosts:
                return True
            return any(ip in net for net in self.trusted_networks)

        except ValueError:
            return host in self.trusted_literals
