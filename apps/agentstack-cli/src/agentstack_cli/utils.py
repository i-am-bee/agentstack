# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
import functools
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from collections.abc import AsyncIterator, Mapping, MutableMapping
from contextlib import asynccontextmanager
from contextvars import ContextVar
from copy import deepcopy
from io import BytesIO
from typing import TYPE_CHECKING, Any

import anyio
import anyio.abc
import httpx
import typer
import yaml
from anyio import create_task_group
from anyio.abc import ByteReceiveStream, TaskGroup
from jsf import JSF
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import CompleteStyle
from pydantic import BaseModel
from rich.console import Capture, Console
from rich.text import Text

from agentstack_cli.console import console, err_console

__all__ = [
    "IN_VERBOSITY_CONTEXT",
    "SHOW_SUCCESS_STATUS",
    "VERBOSE",
    "capture_output",
    "check_json",
    "extract_messages",
    "format_error",
    "format_model",
    "generate_schema_example",
    "get_github_repo_tags",
    "get_httpx_response_error_details",
    "get_local_github_token",
    "is_github_url",
    "merge",
    "parse_env_var",
    "print_httpx_response_error_details",
    "print_log",
    "prompt_user",
    "remove_nullable",
    "run_command",
    "status",
    "verbosity",
]

if TYPE_CHECKING:
    from prompt_toolkit.completion import Completer
    from prompt_toolkit.validation import Validator


def format_model(value: BaseModel | list[BaseModel]) -> str:
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, list):
        return yaml.dump([item.model_dump(mode="json") for item in value])
    return yaml.dump(value.model_dump(mode="json"))


def format_error(name: str, message: str) -> str:
    return f":boom: [bold red]{name}:[/bold red] {message}"


def extract_messages(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [(exc_type, msg) for e in exc.exceptions for exc_type, msg in extract_messages(e)]
    else:
        message = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            with contextlib.suppress(Exception):
                message = str(exc).split(" for url", maxsplit=1)[0]
                message = f"{message}: {exc.response.json()['detail']}"

        return [(type(exc).__name__, message)]


def parse_env_var(env_var: str) -> tuple[str, str]:
    """Parse environment variable string in format NAME=VALUE."""
    if "=" not in env_var:
        raise ValueError(f"Environment variable {env_var} is invalid, use format --env NAME=VALUE")
    key, value = env_var.split("=", 1)
    return key.strip(), value.strip()


def check_json(value: Any) -> dict[str, Any]:
    try:
        return json.loads(value)
    except json.decoder.JSONDecodeError as e:
        raise typer.BadParameter(f"Invalid JSON '{value}'") from e


@functools.cache
def generate_schema_example(json_schema: dict[str, Any]) -> dict[str, Any]:
    json_schema = deepcopy(remove_nullable(json_schema))

    def _make_fakes_better(schema: dict[str, Any] | None):
        if not schema:
            return
        match schema["type"]:
            case "array":
                schema["maxItems"] = 3
                schema["minItems"] = 1
                schema["uniqueItems"] = True
                _make_fakes_better(schema["items"])
            case "object":
                for property in schema["properties"].values():
                    _make_fakes_better(property)

    _make_fakes_better(json_schema)
    return JSF(json_schema, allow_none_optionals=0).generate()


def remove_nullable(schema: dict[str, Any]) -> dict[str, Any]:
    if "anyOf" not in schema and "oneOf" not in schema:
        return schema
    enum_discriminator = "anyOf" if "anyOf" in schema else "oneOf"
    if len(schema[enum_discriminator]) == 2:
        obj1, obj2 = schema[enum_discriminator]
        match (obj1["type"], obj2["type"]):
            case ("null", _):
                return obj2
            case (_, "null"):
                return obj1
            case _:
                return schema
    return schema


prompt_session = None


def prompt_user(
    prompt: str | None = None,
    completer: "Completer | None" = None,
    placeholder: str | None = None,
    validator: "Validator | None" = None,
    open_autocomplete_by_default=False,
) -> str:
    global prompt_session
    # This is necessary because we are in a weird sync-under-async situation and the PromptSession
    # tries calling asyncio.run
    from prompt_toolkit import HTML
    from prompt_toolkit.application.current import get_app
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import DummyCompleter
    from prompt_toolkit.validation import DummyValidator

    if not prompt_session:
        prompt_session = PromptSession()

    def prompt_autocomplete():
        buffer = get_app().current_buffer
        if buffer.complete_state:
            buffer.complete_next()
        else:
            buffer.start_completion(select_first=False)

    if placeholder is None:
        placeholder = "Type your message (/? for help, /q to quit)"

    return prompt_session.prompt(
        prompt or ">>> ",
        auto_suggest=AutoSuggestFromHistory(),
        placeholder=HTML(f"<ansibrightblack> {placeholder}</ansibrightblack>"),
        complete_style=CompleteStyle.COLUMN,
        completer=completer or DummyCompleter(),
        pre_run=prompt_autocomplete if open_autocomplete_by_default else None,
        complete_while_typing=True,
        validator=validator or DummyValidator(),
        in_thread=True,
    )


@asynccontextmanager
async def capture_output(process: anyio.abc.Process, stream_contents: list | None = None) -> AsyncIterator[TaskGroup]:
    async def receive_logs(stream: ByteReceiveStream, index=0):
        buffer = BytesIO()
        async for chunk in stream:
            err_console.print(Text.from_ansi(chunk.decode(errors="replace")), style="dim")
            buffer.write(chunk)
        if stream_contents:
            stream_contents[index] = buffer.getvalue()

    async with create_task_group() as tg:
        if process.stdout:
            tg.start_soon(receive_logs, process.stdout, 0)
        if process.stderr:
            tg.start_soon(receive_logs, process.stderr, 1)
        yield tg


async def run_command(
    command: list[str],
    message: str,
    env: dict[str, str] | None = None,
    cwd: str = ".",
    check: bool = True,
    input: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Helper function to run a subprocess command and handle common errors."""
    env = env or {}
    try:
        with status(message):
            err_console.print(f"Command: {command}", style="dim")
            start_time = time.time()  # Track start time
            async with await anyio.open_process(
                command, stdin=subprocess.PIPE if input else None, env={**os.environ, **env}, cwd=cwd
            ) as process:
                stream_contents: list[bytes | None] = [None, None]
                async with capture_output(process, stream_contents=stream_contents):
                    if process.stdin and input:
                        await process.stdin.send(input)
                        await process.stdin.aclose()
                    await process.wait()

                output, errors = stream_contents
                if check and process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode or 0, command, output, errors)

                total_seconds = int(time.time() - start_time)
                if total_seconds < 5:
                    duration_str = ""
                elif total_seconds < 60:
                    duration_str = f"({total_seconds}s)"
                else:
                    duration_str = f"({total_seconds // 60}m{total_seconds % 60}s)"

                if SHOW_SUCCESS_STATUS.get():
                    console.print(f"{message} [[green]DONE[/green]] [dim]{duration_str}[/dim]")
                return subprocess.CompletedProcess(command, process.returncode or 0, output, errors)
    except FileNotFoundError:
        console.print(f"{message} [[red]ERROR[/red]]")
        tool_name = command[0]
        console.error(f"{tool_name} is not installed. Please install {tool_name} first.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"{message} [[red]ERROR[/red]]")
        err_console.print(f"[red]Exit code: {e.returncode} [/red]")
        if e.stderr:
            err_console.print(f"[red]Error: {e.stderr.strip()}[/red]")
        if e.stdout:
            err_console.print(f"[red]Output: {e.stdout.strip()}[/red]")
        raise


IN_VERBOSITY_CONTEXT: ContextVar[bool] = ContextVar("verbose", default=False)
VERBOSE: ContextVar[bool] = ContextVar("verbose", default=False)
SHOW_SUCCESS_STATUS: ContextVar[bool] = ContextVar("show_command_status", default=True)


@contextlib.contextmanager
def status(message: str):
    if VERBOSE.get():
        console.print(f"{message}...")
        yield
        return
    else:
        err_console.print(f"\n[bold]{message}[/bold]")
        with console.status(f"{message}...", spinner="dots"):
            yield


@contextlib.contextmanager
def verbosity(verbose: bool, show_success_status: bool = True):
    if IN_VERBOSITY_CONTEXT.get():
        yield  # Already in a verbosity context, act as a null context manager
        return

    IN_VERBOSITY_CONTEXT.set(True)
    token = VERBOSE.set(verbose)
    token_command_status = SHOW_SUCCESS_STATUS.set(show_success_status)
    capture: Capture | None = None
    try:
        with err_console.capture() if not verbose else contextlib.nullcontext() as capture:
            yield

    except Exception:
        if not verbose and capture and (logs := capture.get().strip()):
            err_console.print("\n[yellow]--- Captured logs ---[/yellow]\n")
            err_console.print(Text.from_ansi(logs, style="dim"))
            err_console.print("\n[red]------- Error -------[/red]\n")
        raise
    finally:
        VERBOSE.reset(token)
        IN_VERBOSITY_CONTEXT.set(False)
        SHOW_SUCCESS_STATUS.reset(token_command_status)


def print_log(line, ansi_mode=False, out_console: Console | None = None):
    if "error" in line:

        class CustomError(Exception): ...

        CustomError.__name__ = line["error"]["type"]

        raise CustomError(line["error"]["detail"])

    def decode(text: str):
        return Text.from_ansi(text) if ansi_mode else text

    match line:
        case {"stream": "stderr"}:
            (out_console or err_console).print(decode(line["message"]))
        case {"stream": "stdout"}:
            (out_console or console).print(decode(line["message"]))
        case {"event": "[DONE]"}:
            return
        case _:
            (out_console or console).print(line)


# ! This pattern is taken from agentstack_server.utils.github.GithubUrl, make sure to keep it in sync
github_url_verbose_pattern = r"""
        ^
        (?:git\+)?                              # Optional git+ prefix
        https?://(?P<host>github(?:\.[^/]+)+)/  # GitHub host (github.com or github.enterprise.com)
        (?P<org>[^/]+)/                         # Organization
        (?P<repo>
            (?:                                 # Non-capturing group for repo name
                (?!\.git(?:$|[@#]))             # Negative lookahead for .git at end or followed by @#
                [^/@#]                          # Any char except /@#
            )+                                  # One or more of these chars
        )
        (?:\.git)?                              # Optional .git suffix
        (?:@(?P<version>[^#]+))?                # Optional version after @
        (?:\#path=(?P<path>.+))?                # Optional path after #path=
        $
    """


def is_github_url(url: str) -> bool:
    return bool(re.match(github_url_verbose_pattern, url, re.VERBOSE))


def get_local_github_token() -> str | None:
    """Get GitHub token from standard local sources for authenticated API requests.

    Checks multiple sources in order of preference:
    1. GITHUB_TOKEN environment variable
    2. GH_TOKEN environment variable (used by GitHub CLI)
    3. GitHub CLI (gh auth token) if user is logged in

    Authenticated requests have much higher rate limits (5000/hour vs 60/hour).
    """
    # Check environment variables first
    if token := os.getenv("GITHUB_TOKEN"):
        return token
    if token := os.getenv("GH_TOKEN"):
        return token

    # Try GitHub CLI if available
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and (token := result.stdout.strip()):
            return token
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


async def get_github_repo_tags(host: str, owner: str, repo: str) -> list[str]:
    headers = {"Accept": "application/vnd.github.v3+json"}

    # Add authentication if GITHUB_TOKEN is available (avoids rate limiting)
    if token := get_local_github_token():
        headers["Authorization"] = f"token {token}"

    # Determine API host
    if host == "github.com":
        api_host = "api.github.com"
        if not get_local_github_token():
            console.info(
                "No GitHub token found. Using unauthenticated API (60 requests/hour limit).\n"
                "For higher limits, run [green]gh auth login[/green] or set GITHUB_TOKEN or GH_TOKEN env variable."
            )
    else:
        # GitHub Enterprise uses host/api/v3
        api_host = f"{host}/api/v3"

    async with httpx.AsyncClient() as client:
        # Correct format: /repos/{owner}/{repo}/tags
        url = f"https://{api_host}/repos/{owner}/{repo}/tags"
        response = await client.get(url, headers=headers)

        tags = [tag["name"] for tag in response.json()] if response.status_code == 200 else []

        if not tags and response.status_code != 200:
            console.warning(f"Failed to fetch tags from '{url}' (status code {response.status_code}). ")
        elif not tags and response.status_code <= 200:
            console.warning(f"No tags fetched from '{url}' (status code {response.status_code}). ")

        return tags


def get_httpx_response_error_details(response: httpx.Response | None) -> tuple[str, str] | None:
    if response:
        try:
            error_json = response.json()
            return (
                f"error: {error_json.get('error', 'unknown')}",
                f"error description: {error_json.get('error_description', 'No description')}",
            )
        except Exception:
            pass


def print_httpx_response_error_details(resp: httpx.Response | None) -> None:
    error_details = get_httpx_response_error_details(resp)
    if error_details:
        for line in error_details:
            console.error(line)


# Inspired by: https://github.com/clarketm/mergedeep/blob/master/mergedeep/mergedeep.py
def _is_recursive_merge(a: Any, b: Any) -> bool:
    both_mapping = isinstance(a, Mapping) and isinstance(b, Mapping)
    both_counter = isinstance(a, Counter) and isinstance(b, Counter)
    return both_mapping and not both_counter


def _handle_merge_replace(destination, source, key):
    if isinstance(destination[key], Counter) and isinstance(source[key], Counter):
        # Merge both destination and source `Counter` as if they were a standard dict.
        _deepmerge(destination[key], source[key])
    else:
        # If a key exists in both objects and the values are `different`, the value from the `source` object will be used.
        destination[key] = deepcopy(source[key])


def _deepmerge(dst, src):
    for key in src:
        if key in dst:
            if _is_recursive_merge(dst[key], src[key]):
                # If the key for both `dst` and `src` are both Mapping types (e.g. dict), then recurse.
                _deepmerge(dst[key], src[key])
            elif dst[key] is src[key]:
                # If a key exists in both objects and the values are `same`, the value from the `dst` object will be used.
                pass
            else:
                _handle_merge_replace(dst, src, key)
        else:
            # If the key exists only in `src`, the value from the `src` object will be used.
            dst[key] = deepcopy(src[key])
    return dst


def merge(destination: MutableMapping[str, Any], *sources: Mapping[str, Any]) -> MutableMapping[str, Any]:
    """
    A deep merge function for 🐍.

    :param destination: The destination mapping.
    :param sources: The source mappings.
    :return:
    """
    return functools.reduce(_deepmerge, sources, destination)
