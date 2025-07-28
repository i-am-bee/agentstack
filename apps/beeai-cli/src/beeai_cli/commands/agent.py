# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc
import base64
import inspect
import json
import random
import re
import sys
import typing
from enum import StrEnum
from uuid import uuid4

import httpx
import jsonref
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)
from pydantic import BaseModel, computed_field
from rich.box import HORIZONTALS
from rich.console import ConsoleRenderable, Group, NewLine
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from beeai_cli.commands.build import build
from beeai_cli.commands.env import ensure_llm_env

if sys.platform != "win32":
    try:
        # This is necessary for proper handling of arrow keys in interactive input
        import gnureadline as readline
    except ImportError:
        import readline  # noqa: F401

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema
import rich.json
import typer
from rich.markdown import Markdown
from rich.table import Column

from beeai_cli.api import a2a_client, api_request, api_stream
from beeai_cli.async_typer import AsyncTyper, console, create_table, err_console
from beeai_cli.utils import (
    format_error,
    generate_schema_example,
    omit,
    prompt_user,
    remove_nullable,
    run_command,
    status,
    verbosity,
)


class UiType(StrEnum):
    chat = "chat"
    hands_off = "hands-off"


class Provider(BaseModel):
    agent_card: AgentCard
    id: str
    metadata: dict[str, Any]

    @computed_field
    @property
    def ui_annotations(self) -> dict[str, str] | None:
        ui_extension = [ext for ext in self.agent_card.capabilities.extensions or [] if ext.uri == "beeai_ui"]
        return ui_extension[0].params if ui_extension else None

    @computed_field
    @property
    def last_error(self) -> str | None:
        return (
            (self.metadata.get("last_error") or {}).get("message", None) if self.metadata["state"] != "ready" else None
        )

    @computed_field
    @property
    def short_location(self) -> str:
        return re.sub(r"[a-z]*.io/i-am-bee/beeai-platform/", "", self.metadata["source"]).lower()


app = AsyncTyper()

processing_messages = [
    "Buzzing with ideas...",
    "Pollinating thoughts...",
    "Honey of an answer coming up...",
    "Swarming through data...",
    "Bee-processing your request...",
    "Hive mind activating...",
    "Making cognitive honey...",
    "Waggle dancing for answers...",
    "Bee right back...",
    "Extracting knowledge nectar...",
]


def _print_log(line, ansi_mode=False):
    if "error" in line:

        class CustomError(Exception): ...

        CustomError.__name__ = line["error"]["type"]

        raise CustomError(line["error"]["detail"])

    def decode(text: str):
        return Text.from_ansi(text) if ansi_mode else text

    if line["stream"] == "stderr":
        err_console.print(decode(line["message"]))
    elif line["stream"] == "stdout":
        console.print(decode(line["message"]))


@app.command("add")
async def add_agent(
    location: typing.Annotated[
        str, typer.Argument(help="Agent location (public docker image, local path or github url)")
    ],
    vm_name: typing.Annotated[str, typer.Option(hidden=True)] = "beeai-platform",
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
) -> None:
    """Install discovered agent or add public docker image or github repository [aliases: install]"""
    agent_card = None
    # Try extracting manifest locally for local images

    with verbosity(verbose):
        process = await run_command(["docker", "inspect", location], check=False, message="Inspecting docker images.")
        from subprocess import CalledProcessError

        errors = []

        try:
            if process.returncode:
                # If the image was not found locally, try building image
                location, agent_card = await build(location, tag=None, vm_name=vm_name, import_image=True)
            else:
                manifest = base64.b64decode(
                    json.loads(process.stdout)[0]["Config"]["Labels"]["beeai.dev.agent.json"]
                ).decode()
                agent_card = json.loads(manifest)
            # If all build and inspect succeeded, use the local image, else use the original; maybe it exists remotely
        except CalledProcessError as e:
            errors.append(e)
            console.print("Attempting to use remote image...")
        try:
            with status("Registering agent to platform"):
                await api_request("POST", "providers", json={"location": location, "agent_card": agent_card})
            console.print("Registering agent to platform [[green]DONE[/green]]")
        except Exception as e:
            raise ExceptionGroup("Error occured", [*errors, e]) from e
        await list_agents()


def select_provider(search_path: str, providers: list[Provider]):
    search_path = search_path.lower()
    provider_candidates = {p.id: p for p in providers if search_path in p.id.lower()}
    provider_candidates.update({p.id: p for p in providers if search_path in p.agent_card.name.lower()})
    provider_candidates.update({p.id: p for p in providers if search_path in p.short_location})
    if len(provider_candidates) != 1:
        provider_candidates = [f"  - {c}" for c in provider_candidates]
        remove_providers_detail = ":\n" + "\n".join(provider_candidates) if provider_candidates else ""
        raise ValueError(f"{len(provider_candidates)} matching agents{remove_providers_detail}")
    [selected_provider] = provider_candidates.values()
    return selected_provider


@app.command("remove | uninstall | rm | delete")
async def uninstall_agent(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
) -> None:
    """Remove agent"""
    with console.status("Uninstalling agent (may take a few minutes)...", spinner="dots"):
        remove_provider = select_provider(search_path, await get_providers()).id
        await api_request("delete", f"providers/{remove_provider}")
    await list_agents()


@app.command("logs")
async def stream_logs(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
):
    """Stream agent provider logs"""
    provider = select_provider(search_path, await get_providers()).id
    async for message in api_stream("get", f"providers/{provider}/logs"):
        _print_log(message)


async def _run_agent(
    client: A2AClient,
    input: str | Message,
    dump_files_path: Path | None = None,
    handle_input: Callable[[], str] | None = None,
    task_id: str | None = None,
    context_id: str | None = None,
) -> tuple[str | None, str | None]:
    status = console.status(random.choice(processing_messages), spinner="dots")
    status.start()
    status_stopped = False

    input = (
        Message(
            messageId=str(uuid4()),
            parts=[Part(root=TextPart(text=input))],
            role=Role.user,
            taskId=task_id,
            contextId=context_id,
        )
        if isinstance(input, str)
        else input
    )

    log_type = None

    request = SendStreamingMessageRequest(id=str(uuid4()), params=MessageSendParams(message=input))
    stream = client.send_message_streaming(request)

    while True:
        async for event in stream:
            if not status_stopped:
                status_stopped = True
                status.stop()
            match event.root:
                case SendStreamingMessageSuccessResponse():
                    task_id = getattr(event.root.result, "taskId", None)
                    context_id = getattr(event.root.result, "contextId", None)
                    match event.root.result:
                        case Task(id=tid, contextId=cid):
                            # Handle task creation
                            task_id = tid
                            context_id = cid
                        case Message():
                            # Handle message response - check for update_kind metadata
                            message = event.root.result
                            update_kind = None

                            # Check for update_kind in message metadata
                            if update_kind := (message.metadata or {}).get("update_kind"):
                                # This is a streaming update with a specific type
                                if update_kind != log_type:
                                    if log_type is not None:
                                        err_console.print()
                                    err_console.print(f"{update_kind}: ", style="dim", end="")
                                    log_type = update_kind

                                # Stream the content
                                for part in message.parts:
                                    if hasattr(part.root, "text"):
                                        err_console.print(part.root.text, style="dim", end="")
                            else:
                                # This is regular message content
                                if log_type:
                                    console.print()
                                    log_type = None
                                for part in message.parts:
                                    if hasattr(part.root, "text"):
                                        console.print(part.root.text, end="")
                        case TaskStatusUpdateEvent(status=task_status):
                            match task_status.state:
                                case TaskState.completed:
                                    console.print()  # Add newline after completion
                                    return None, context_id
                                case TaskState.submitted:
                                    pass
                                case TaskState.working:
                                    # Handle streaming content during working state
                                    if hasattr(task_status, "message") and task_status.message:
                                        message = task_status.message
                                        update_kind = (message.metadata or {}).get("update_kind")
                                        if update_kind and update_kind != "final_answer":
                                            if update_kind != log_type:
                                                if log_type is not None:
                                                    err_console.print()
                                                err_console.print(f"{update_kind}: ", style="dim", end="")
                                                log_type = update_kind

                                            # Stream the content
                                            for part in message.parts:
                                                if hasattr(part.root, "text"):
                                                    err_console.print(part.root.text, style="dim", end="")
                                        else:
                                            # This is regular message content
                                            if log_type:
                                                console.print()
                                                log_type = None
                                            for part in message.parts:
                                                if hasattr(part.root, "text"):
                                                    console.print(part.root.text, end="")
                                case TaskState.input_required:
                                    if handle_input is None:
                                        raise ValueError("Agent requires input but no input handler provided")

                                    console.print("\n[bold]Agent requires your input[/bold]\n")
                                    user_input = handle_input()

                                    # Send the user input back to the agent
                                    response_message = Message(
                                        messageId=str(uuid4()),
                                        parts=[Part(root=TextPart(text=user_input))],
                                        role=Role.user,
                                        taskId=task_id,
                                        contextId=context_id,
                                    )
                                    new_request = SendStreamingMessageRequest(
                                        id=str(uuid4()), params=MessageSendParams(message=response_message)
                                    )
                                    stream = client.send_message_streaming(new_request)
                                    break
                                case TaskState.canceled:
                                    console.print("[yellow]Task was canceled[/yellow]")
                                    return task_id, context_id
                                case TaskState.failed:
                                    message = task_status.message.parts[0].root.text if task_status.message else ""
                                    console.print(f"[red]Task failed[/red]: {message}")
                                    return task_id, context_id
                                case TaskState.rejected:
                                    console.print("[red]Task was rejected[/red]")
                                    return task_id, context_id
                                case TaskState.auth_required:
                                    console.print("[yellow]Authentication required[/yellow]")
                                    return task_id, context_id
                                case TaskState.unknown:
                                    console.print("[yellow]Unknown task status[/yellow]")
                        case TaskArtifactUpdateEvent():
                            artifact = event.root.result.artifact
                            if dump_files_path is None:
                                continue
                            dump_files_path.mkdir(parents=True, exist_ok=True)
                            full_path = dump_files_path / artifact.name.lstrip("/")
                            full_path.resolve().relative_to(dump_files_path.resolve())
                            full_path.parent.mkdir(parents=True, exist_ok=True)
                            try:
                                for part in artifact.parts[:1]:
                                    match part.root:
                                        case FilePart():
                                            match part.root.file:
                                                case FileWithBytes(bytes=bytes):
                                                    full_path.write_bytes(base64.b64decode(bytes))
                                                case FileWithUri(uri=uri):
                                                    async with httpx.AsyncClient() as client:
                                                        resp = await client.get(uri)
                                                        full_path.write_bytes(base64.b64decode(resp.content))
                                            console.print(f"📁 Saved {full_path}")
                                        case TextPart(text=text):
                                            full_path.write_text(text)
                                        case _:
                                            console.print(f"⚠️ Artifact part {type(part).__name__} is not supported")
                                if len(artifact.parts) > 1:
                                    console.print("⚠️ Artifact with more than 1 part are not supported.")
                            except ValueError:
                                console.print(f"⚠️ Skipping artifact {artifact.name} - outside dump directory")
                case JSONRPCErrorResponse():
                    console.print(format_error(str(type(event.root.error)), event.root.error.message))
                    return task_id, context_id
        else:
            # Stream ended normally
            break
    return task_id, context_id


class InteractiveCommand(abc.ABC):
    args: typing.ClassVar[list[str]] = []
    command: str

    @abc.abstractmethod
    def handle(self, args_str: str | None = None): ...

    @property
    def enabled(self) -> bool:
        return True

    def completion_opts(self) -> dict[str, Any | None] | None:
        return None


class Quit(InteractiveCommand):
    """Quit"""

    command = "q"

    def handle(self, *_any):
        sys.exit(0)


class ShowConfig(InteractiveCommand):
    """Show available and currently set configuration options"""

    command = "show-config"

    def __init__(self, config_schema: dict[str, Any] | None, config: dict[str, Any]):
        self.config_schema = config_schema
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(self.config_schema)

    def handle(self, *_any):
        with create_table(Column("Key", ratio=1), Column("Type", ratio=3), Column("Example", ratio=2)) as schema_table:
            for prop, schema in self.config_schema["properties"].items():
                required_schema = remove_nullable(schema)
                schema_table.add_row(
                    prop,
                    json.dumps(required_schema),
                    json.dumps(generate_schema_example(required_schema)),
                )

        renderables = [
            NewLine(),
            Panel(schema_table, title="Configuration schema", title_align="left"),
        ]

        if self.config:
            with create_table(Column("Key", ratio=1), Column("Value", ratio=5)) as config_table:
                for key, value in self.config.items():
                    config_table.add_row(key, json.dumps(value))
            renderables += [
                NewLine(),
                Panel(config_table, title="Current configuration", title_align="left"),
            ]
        panel = Panel(
            Group(
                *renderables,
                NewLine(),
                console.render_str("[b]Hint[/b]: Use /set <key> <value> to set an agent configuration property."),
            ),
            title="Agent configuration",
            box=HORIZONTALS,
        )
        console.print(panel)


class Set(InteractiveCommand):
    """Set agent configuration value. Use JSON syntax for more complex objects"""

    args: typing.ClassVar[list[str]] = ["<key>", "<value>"]
    command = "set"

    def __init__(self, config_schema: dict[str, Any] | None, config: dict[str, Any]):
        self.config_schema = config_schema
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(self.config_schema)

    def handle(self, args_str: str | None = None):
        args_str = args_str or ""
        args = args_str.split(" ", maxsplit=1)
        if not args_str or len(args) != 2:
            raise ValueError(f"The command {self.command} takes exactly two arguments: <key> and <value>.")
        key, value = args
        if key not in self.config_schema["properties"]:
            raise ValueError(f"Unknown option {key}")
        try:
            if value.strip("\"'") == value and not value.startswith("{") and not value.startswith("["):
                value = f'"{value}"'
            json_value = json.loads(value)
            tmp_config = {**self.config, key: json_value}
            jsonschema.validate(tmp_config, self.config_schema)
            self.config[key] = json_value
            console.print("Config:", self.config)
        except json.JSONDecodeError as ex:
            raise ValueError(f"The provided value cannot be parsed into JSON: {value}") from ex
        except jsonschema.ValidationError as ex:
            err_console.print(json.dumps(generate_schema_example(self.config_schema["properties"][key])))
            raise ValueError(f"Invalid value for key {key}: {ex}") from ex

    def completion_opts(self) -> dict[str, Any | None] | None:
        return {
            key: {json.dumps(generate_schema_example(schema))}
            for key, schema in self.config_schema["properties"].items()
        }


class Help(InteractiveCommand):
    """Show this help."""

    command = "?"

    def __init__(self, commands: list[InteractiveCommand], splash_screen: ConsoleRenderable | None = None):
        [self.config_command] = [command for command in commands if isinstance(command, ShowConfig)] or [None]
        self.splash_screen = splash_screen
        self.commands = [self, *commands]

    def handle(self, *_any):
        if self.splash_screen:
            console.print(self.splash_screen)
        if self.config_command:
            self.config_command.handle()
        console.print()
        with create_table("command", "arguments", "description") as table:
            for command in self.commands:
                table.add_row(f"/{command.command}", " ".join(command.args or ["n/a"]), inspect.getdoc(command))
        console.print(table)


def _create_input_handler(
    commands: list[InteractiveCommand],
    prompt: str | None = None,
    choice: list[str] | None = None,
    optional: bool = False,
    placeholder: str | None = None,
    splash_screen: ConsoleRenderable | None = None,
) -> Callable:
    choice = choice or []
    commands = [cmd for cmd in commands if cmd.enabled]
    commands = [Quit(), *commands]
    commands = [Help(commands, splash_screen=splash_screen), *commands]
    commands_router = {f"/{cmd.command}": cmd for cmd in commands}
    completer = {
        **{f"/{cmd.command}": cmd.completion_opts() for cmd in commands},
        **dict.fromkeys(choice),
    }

    valid_options = set(choice) | commands_router.keys()

    def validate(text: str):
        if optional and not text:
            return True
        return text in valid_options if choice else bool(text)

    def handler():
        from prompt_toolkit.completion import NestedCompleter
        from prompt_toolkit.validation import Validator

        while True:
            try:
                input = prompt_user(
                    prompt=prompt,
                    placeholder=placeholder,
                    completer=NestedCompleter.from_nested_dict(completer),
                    validator=Validator.from_callable(validate),
                    open_autocomplete_by_default=bool(choice),
                )
                if input.startswith("/"):
                    command, *arg_str = input.split(" ", maxsplit=1)
                    if command not in commands_router:
                        raise ValueError(f"Unknown command: {command}")
                    commands_router[command].handle(*arg_str)
                    continue
                return input
            except ValueError as exc:
                err_console.print(str(exc))
            except EOFError as exc:
                raise KeyboardInterrupt from exc

    return handler


def _setup_sequential_workflow(providers: list[Provider], splash_screen: ConsoleRenderable | None = None):
    prompt_agents = {
        provider.agent_card.name: provider
        for provider in providers
        if (provider.ui_annotations or {}).get("ui_type") == UiType.hands_off
    }
    steps = []

    console.print(Rule(title="Configure Workflow", style="white"))

    handle_input = _create_input_handler(
        [], prompt="Agent: ", choice=list(prompt_agents), placeholder="Select agent", splash_screen=splash_screen
    )
    handle_instruction_input = _create_input_handler(
        [], prompt="Instruction: ", placeholder="Enter agent instruction", splash_screen=splash_screen
    )
    i = 0

    while True:
        if not (agent := handle_input()):
            console.print(Rule(style="white"))
            break
        instruction = handle_instruction_input()

        if not steps:
            # change prompt for other passes
            handle_input = _create_input_handler(
                [],
                prompt="Agent: ",
                placeholder="Select agent (Leave empty to execute)",
                choice=list(prompt_agents),
                optional=True,
                splash_screen=splash_screen,
            )
            handle_instruction_input = _create_input_handler(
                [],
                prompt="Instruction: ",
                placeholder="Enter agent instruction (leave empty to pass raw output from previous agent)",
                optional=True,
                splash_screen=splash_screen,
            )
        console.print(Rule(style="dim", characters="·"))
        i += 1
        steps.append({"agent": agent, "instruction": instruction})

    return steps


def _get_config_schema(schema: dict[str, Any] | None) -> dict[str, Any] | None:
    if not schema:
        return None
    schema = jsonref.replace_refs(schema, lazy_load=False)

    if not (schema := schema.get("properties", {}).get("config", None)):
        return None

    schema = remove_nullable(schema)
    if not schema.get("properties", None):
        return None
    return schema


async def get_provider(provider_id: str):
    return await api_request("GET", f"providers/{provider_id}")


@app.command("run")
async def run_agent(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
    input: typing.Annotated[
        str | None,
        typer.Argument(
            default_factory=lambda: None if sys.stdin.isatty() else sys.stdin.read(),
            help="Agent input as text or JSON",
        ),
    ],
    dump_files: typing.Annotated[
        Path | None, typer.Option(help="Folder path to save any files returned by the agent")
    ] = None,
) -> None:
    """Run an agent."""
    await ensure_llm_env()

    providers = await get_providers()
    provider = select_provider(search_path, providers=providers)
    agent = provider.agent_card

    if provider.metadata["state"] == "missing":
        console.print("Starting provider (this might take a while)...")
    if provider.metadata["state"] not in {"ready", "running", "starting", "missing"}:
        err_console.print(
            f":boom: Agent is not in a ready state: {provider['state']}, {provider['last_error']}\nRetrying..."
        )

    ui_annotations = provider.ui_annotations or {}
    ui_type = ui_annotations.get("ui_type")
    is_sequential_workflow = agent.name in {"sequential_workflow"}

    user_greeting = ui_annotations.get("user_greeting", None) or "How can I help you?"

    if not input:
        if ui_type not in {UiType.chat, UiType.hands_off} and not is_sequential_workflow:
            err_console.print(
                f"💥 [red][b]Error[/red][/b]: Agent {agent.name} does not use any supported UIs.\n"
                f"Please use the agent according to the following examples and schema:"
            )
            err_console.print(_render_examples(agent))
            exit(1)

        splash_screen = Group(
            Markdown(f"# {agent.name}  \n{agent.description}"),
            NewLine(),
        )

        handle_input = _create_input_handler([], splash_screen=splash_screen)

        if ui_type == UiType.chat:
            console.print(f"{user_greeting}\n")
            input = handle_input()
            async with a2a_client(provider.agent_card) as client:
                task_id, context_id = None, None
                while True:
                    console.print()
                    task_id, context_id = await _run_agent(
                        client,
                        input,
                        dump_files_path=dump_files,
                        handle_input=handle_input,
                        task_id=task_id,
                        context_id=context_id,
                    )
                    console.print()
                    input = handle_input()

        elif ui_type == UiType.hands_off:
            user_greeting = ui_annotations.get("user_greeting", None) or "Enter your instructions."
            console.print(f"{user_greeting}\n")
            input = handle_input()
            console.print()
            async with a2a_client(provider.agent_card) as client:
                await _run_agent(client, input, dump_files_path=dump_files, handle_input=handle_input)
        elif is_sequential_workflow:
            workflow_steps = _setup_sequential_workflow(providers, splash_screen=splash_screen)
            console.print()
            message_part = DataPart(data={"steps": workflow_steps}, metadata={"kind": "configuration"})
            async with a2a_client(provider.agent_card) as client:
                await _run_agent(
                    client,
                    Message(
                        messageId=str(uuid4()),
                        parts=[Part(root=message_part)],
                        role=Role.user,
                    ),
                    dump_files_path=dump_files,
                    handle_input=handle_input,
                )

    else:
        async with a2a_client(provider.agent_card) as client:
            await _run_agent(client, input, dump_files_path=dump_files)


def render_enum(value: str, colors: dict[str, str]) -> str:
    if color := colors.get(value):
        return f"[{color}]{value}[/{color}]"
    return value


async def get_providers() -> list[Provider]:
    return [
        Provider(
            agent_card=provider["agent_card"],
            id=provider["id"],
            metadata=omit(provider, {"agent_card"}),
        )
        for provider in (await api_request("GET", "providers"))["items"]
    ]


@app.command("list")
async def list_agents():
    """List agents."""
    providers = await get_providers()
    max_provider_len = max(len(p.short_location) for p in providers) if providers else 0
    max_error_len = max(len(p.last_error or "") for p in providers) if providers else 0

    def _sort_fn(provider: Provider):
        state = {"missing": "1"}
        return (
            str(state.get(provider.metadata["state"], 0)) + f"_{provider.agent_card.name}"
            if "registry" in provider
            else provider.agent_card.name
        )

    with create_table(
        Column("Short ID", style="yellow"),
        Column("Name", style="yellow"),
        Column("State", width=len("starting")),
        Column("Description", ratio=2),
        Column("UI"),
        Column("Location", max_width=min(max(max_provider_len, len("Location")), 70)),
        Column("Missing Env", max_width=50),
        Column("Last Error", max_width=min(max(max_error_len, len("Last Error")), 50)),
        no_wrap=True,
    ) as table:
        for provider in sorted(providers, key=_sort_fn):
            state = None
            missing_env = None
            state = provider.metadata["state"]
            missing_env = ",".join(var["name"] for var in provider.metadata["missing_configuration"])
            table.add_row(
                provider.id[:8],
                provider.agent_card.name,
                render_enum(
                    state or "<unknown>",
                    {
                        "running": "green",
                        "ready": "blue",
                        "starting": "blue",
                        "missing": "grey",
                        "error": "red",
                    },
                ),
                (provider.agent_card.description or "<none>").replace("\n", " "),
                (provider.ui_annotations or {}).get("ui_type") or "<none>",
                provider.short_location or "<none>",
                missing_env or "<none>",
                provider.last_error or "<none>",
            )
    console.print(table)


def _render_schema(schema: dict[str, Any] | None):
    return "No schema provided." if not schema else rich.json.JSON.from_data(schema)


def _render_examples(agent: AgentCard):
    # TODO
    return Text()
    #     md = "## Examples"
    #     for i, example in enumerate(examples):
    #         processing_steps = "\n".join(
    #             f"{i + 1}. {step}" for i, step in enumerate(example.get("processing_steps", []) or [])
    #         )
    #         name = example.get("name", None) or f"Example #{i + 1}"
    #         output = f"""
    # ### Output
    # ```
    # {example.get("output", "")}
    # ```
    # """
    #         md += f"""
    # ### {name}
    # {example.get("description", None) or ""}
    #
    # #### Command
    # ```sh
    # {example["command"]}
    # ```
    # {output if example.get("output", None) else ""}
    #
    # #### Processing steps
    # {processing_steps}
    # """
    # return Markdown(md)


@app.command("info")
async def agent_detail(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
):
    """Show agent details."""
    provider = select_provider(search_path, await get_providers())
    agent = provider.agent_card

    basic_info = f"# {agent.name}\n{agent.description}"

    console.print(Markdown(basic_info), "")
    console.print(Markdown("## Skills"))
    console.print()
    for skill in agent.skills:
        console.print(Markdown(f"**{skill.name}**  \n{skill.description}"))

    console.print(_render_examples(agent))

    with create_table(Column("Key", ratio=1), Column("Value", ratio=5), title="Extra information") as table:
        for key, value in omit(agent.model_dump(), {"description", "examples"}).items():
            if value:
                table.add_row(key, str(value))
    console.print()
    console.print(table)

    with create_table(Column("Key", ratio=1), Column("Value", ratio=5), title="Provider") as table:
        for key, value in omit(provider, {"image_id", "manifest", "source", "registry"}).items():
            table.add_row(key, str(value))
    console.print()
    console.print(table)
