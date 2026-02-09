# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import functools
import importlib.metadata
import pathlib
import re
import sys
import typing
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pydantic
import pydantic_settings
from agentstack_sdk.platform import PlatformClient, use_platform_client
from authlib.oauth2.rfc6749.errors import InvalidGrantError, OAuth2Error
from pydantic import HttpUrl, SecretStr

from agentstack_cli.auth_manager import AuthManager
from agentstack_cli.console import console


@functools.cache
def version():
    # Python strips '-', we need to re-insert it: 1.2.3rc1 -> 1.2.3-rc1
    return re.sub(r"([0-9])([a-z])", r"\1-\2", importlib.metadata.version("agentstack-cli"))


@functools.cache
class Configuration(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=None, env_prefix="AGENTSTACK__", env_nested_delimiter="__", extra="allow"
    )
    debug: bool = False
    home: pathlib.Path = pydantic.Field(default_factory=lambda: pathlib.Path.home() / ".agentstack")
    agent_registry: pydantic.AnyUrl = HttpUrl(
        f"https://github.com/i-am-bee/agentstack@v{version()}#path=agent-registry.yaml"
    )
    username: str = "admin"
    password: SecretStr | None = None
    server_metadata_ttl: int = 86400

    oidc_enabled: bool = False
    client_id: str | None = None
    client_secret: str | None = None

    @property
    def lima_home(self) -> pathlib.Path:
        return self.home / "lima"

    @property
    def auth_file(self) -> pathlib.Path:
        """Return auth config file path"""
        return self.home / "auth.json"

    @property
    def auth_manager(self) -> AuthManager:
        return AuthManager(self.auth_file)

    @asynccontextmanager
    async def use_platform_client(self) -> AsyncIterator[PlatformClient]:
        if self.auth_manager.active_server is None:
            console.error("No server selected.")
            console.hint(
                "Run [green]agentstack platform start[/green] to start a local server, or [green]agentstack server login[/green] to connect to a remote one."
            )
            sys.exit(1)

        re_auth_message = (
            f"Run [green]agentstack server login {self.auth_manager.active_server}[/green] to re-authenticate."
        )
        try:
            auth_token = await self.auth_manager.load_auth_token()
        except InvalidGrantError:
            console.error("Your session has expired.")
            console.hint(re_auth_message)
            sys.exit(1)
        except OAuth2Error as e:
            console.error(f"OAuth2 error: {e.description}")
            console.hint(re_auth_message)
            sys.exit(1)
        except RuntimeError as e:
            console.error(f"Failed to load authentication: {e}")
            console.hint("Check your network connection and try again.")
            sys.exit(1)

        async with use_platform_client(
            auth=(self.username, self.password.get_secret_value()) if self.password else None,
            auth_token=auth_token,
            base_url=(self.auth_manager.active_server or "") + "/",
        ) as client:
            yield client

    @pydantic.model_validator(mode="after")
    def _check_old_home(self) -> typing.Self:
        old_home = pathlib.Path.home() / ".beeai"
        if old_home.exists() and not self.home.exists():
            old_home.rename(self.home)
        return self
