# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import contextlib
import functools
import json
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from copy import deepcopy
from io import BytesIO
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import anyio
import anyio.abc
import typer
import yaml
from anyio import create_task_group
from anyio.abc import ByteReceiveStream, TaskGroup
from jsf import JSF
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import CompleteStyle
from pydantic import BaseModel
from rich.console import Capture
from rich.text import Text

from beeai_cli.console import console, err_console

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
        return [(type(exc).__name__, str(exc))]


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
            err_console.print(Text.from_ansi(chunk.decode()), style="dim")
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

                if SHOW_SUCCESS_STATUS.get():
                    console.print(f"{message} [[green]DONE[/green]]")
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


def make_safe_name(resource_url: str) -> str:
    parsed = urlparse(resource_url)
    return parsed.netloc or parsed.path
