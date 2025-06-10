# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import base64
import contextlib
import inspect
import json
import random
import re
import sys
import typing
from enum import StrEnum

import jsonref
from acp_sdk import (
    ACPError,
    Agent,
    ArtifactEvent,
    Error,
    ErrorCode,
    GenericEvent,
    Message,
    MessageAwaitResume,
    MessageCompletedEvent,
    MessagePart,
    MessagePartEvent,
    RunAwaitingEvent,
    RunFailedEvent,
)
from acp_sdk.client import Client
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

from beeai_cli.api import acp_client, api_request, api_stream
from beeai_cli.async_typer import AsyncTyper, console, create_table, err_console
from beeai_cli.utils import (
    VMDriver,
    filter_dict,
    format_error,
    generate_schema_example,
    omit,
    prompt_user,
    remove_nullable,
    run_command,
    verbosity,
)


class UiType(StrEnum):
    chat = "chat"
    hands_off = "hands-off"


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
    vm_driver: typing.Annotated[VMDriver | None, typer.Option(hidden=True)] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", help="Show verbose output")] = False,
) -> None:
    """Install discovered agent or add public docker image or github repository [aliases: install]"""
    agents = None
    # Try extracting manifest locally for local images

    with verbosity(verbose):
        process = await run_command(["docker", "inspect", location], check=False, message="Inspecting docker images.")
        if process.returncode:
            # If the image was not found locally, try building image
            location, agents = await build(location, tag=None, vm_name=vm_name, vm_driver=vm_driver, import_image=True)
        else:
            manifest = base64.b64decode(
                json.loads(process.stdout)[0]["Config"]["Labels"]["beeai.dev.agent.yaml"]
            ).decode()
            agents = json.loads(manifest)["agents"]
        # If all build and inspect succeeded, use the local image, else use the original; maybe it exists remotely
        await api_request("POST", "providers", json={"location": location, "agents": agents})
        await list_agents()


@app.command("remove | uninstall | rm | delete")
async def uninstall_agent(name: typing.Annotated[str, typer.Argument(help="Agent name")]) -> None:
    """Remove agent"""
    agent = await _get_agent(name)
    with console.status("Uninstalling agent (may take a few minutes)...", spinner="dots"):
        await api_request("delete", f"providers/{agent.metadata.provider_id}")
    await list_agents()


@app.command("logs")
async def stream_logs(name: typing.Annotated[str, typer.Argument(help="Agent name")]):
    """Stream agent provider logs"""
    agent = await _get_agent(name)
    provider = agent.metadata.provider_id
    async for message in api_stream("get", f"providers/{provider}/logs"):
        _print_log(message)


async def _run_agent(
    client: Client,
    name: str,
    input: str | list[Message],
    dump_files_path: Path | None = None,
    handle_input: Callable[[], str] | None = None,
):
    status = console.status(random.choice(processing_messages), spinner="dots")
    status.start()
    status_stopped = False

    input = [Message(parts=[MessagePart(content=input, role="user")])] if isinstance(input, str) else input

    log_type = None
    current_agent = None

    stream = client.run_stream(agent=name, input=input)
    while True:
        async for event in stream:
            if not status_stopped:
                status_stopped = True
                status.stop()

            match event:
                case GenericEvent():
                    data = filter_dict(event.generic.model_dump(), None)
                    if "agent_name" in data:
                        (new_log_type, content) = next(iter(omit(data, {"agent_name", "agent_idx"}).items()))
                        new_log_type = f"[{data['agent_name']}]: {new_log_type}"
                    else:
                        (new_log_type, content) = next(iter(data.items()))
                    if new_log_type != log_type:
                        if log_type is not None:
                            err_console.print()
                        err_console.print(f"{new_log_type}: ", style="dim", end="")
                        log_type = new_log_type
                    err_console.print(content, style="dim", end="")
                case MessagePartEvent():
                    if log_type:
                        console.print()
                        log_type = None
                    if new_agent := event.part.model_dump().get("agent_name", None):
                        if new_agent != current_agent:
                            current_agent = new_agent
                            err_console.print(f"\n[bold]{new_agent} output[/bold]\n", style="dim")
                        err_console.print(event.part.content, style="dim", end="")
                    else:
                        console.print(event.part.content, end="")
                case MessageCompletedEvent():
                    console.print()
                case RunAwaitingEvent():
                    assert event.run.await_request is not None

                    if handle_input is None:
                        raise ValueError("Agents awaiting are not supported in the given environment.")

                    console.print(f"\n[bold]Agent '{event.run.agent_name}' requires your action[/bold]\n")
                    console.print(str(event.run.await_request.message))

                    resume_message = Message(parts=[MessagePart(content=handle_input(), role="user")])
                    stream = client.run_resume_stream(
                        MessageAwaitResume(message=resume_message), run_id=event.run.run_id
                    )
                    break
                case RunFailedEvent():
                    console.print(format_error(event.run.error.code.value, event.run.error.message))
                case ArtifactEvent():
                    if dump_files_path is None:
                        continue
                    dump_files_path.mkdir(parents=True, exist_ok=True)
                    full_path = dump_files_path / event.part.name.lstrip("/")
                    with contextlib.suppress(ValueError):
                        full_path.resolve().relative_to(dump_files_path.resolve())  # throws if outside folder
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        if event.part.content_url:
                            err_console.print(
                                f"⚠️ Downloading files is not supported by --dump-files, skipping {event.part.name} ({event.part.content_url})"
                            )
                        elif event.part.content_encoding == "base64":
                            full_path.write_bytes(base64.b64decode(event.part.content))
                            console.print(f"📁 Saved {full_path}")
                        elif event.part.content_encoding == "plain" or not event.part.content_encoding:
                            full_path.write_text(event.part.content)
                            console.print(f"📁 Saved {full_path}")
                        else:
                            err_console.print(
                                f"⚠️ Unknown encoding {event.part.content_encoding}, skipping {event.part.name}"
                            )
        else:
            break


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


def _setup_sequential_workflow(agents_by_name: dict[str, Agent], splash_screen: ConsoleRenderable | None = None):
    prompt_agents = {
        name: agent
        for name, agent in agents_by_name.items()
        if (agent.metadata.model_dump().get("ui", {}) or {}).get("type", None) == UiType.hands_off
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
    name: typing.Annotated[str, typer.Argument(help="Name of the agent to call")],
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

    agents_by_name = await _get_agents()
    agent = await _get_agent(name, agents_by_name)

    # Agent#provider is only available in platform, not when directly communicating with the agent
    if hasattr(agent.metadata, "provider_id"):
        provider = await get_provider(agent.metadata.provider_id)
        if provider["state"] == "missing":
            console.print("Starting provider (this might take a while)...")
        if provider["state"] not in {"ready", "running", "starting", "missing"}:
            err_console.print(
                f":boom: Agent is not in a ready state: {provider['state']}, {provider['last_error']}\nRetrying..."
            )

    ui = agent.metadata.model_dump().get("ui", {}) or {}
    ui_type = ui.get("type", None)
    is_sequential_workflow = agent.name in {"sequential_workflow"}

    user_greeting = ui.get("user_greeting", None) or "How can I help you?"

    if not input:
        if ui_type not in {UiType.chat, UiType.hands_off} and not is_sequential_workflow:
            err_console.print(
                f"💥 [red][b]Error[/red][/b]: Agent {name} does not use any supported UIs.\n"
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
            async with acp_client() as client, client.session() as session:
                while True:
                    console.print()
                    await _run_agent(session, name, input, dump_files_path=dump_files, handle_input=handle_input)
                    console.print()
                    input = handle_input()

        elif ui_type == UiType.hands_off:
            user_greeting = ui.get("user_greeting", None) or "Enter your instructions."
            console.print(f"{user_greeting}\n")
            input = handle_input()
            console.print()
            async with acp_client() as client:
                await _run_agent(client, name, input, dump_files_path=dump_files, handle_input=handle_input)
        elif is_sequential_workflow:
            workflow_steps = _setup_sequential_workflow(agents_by_name, splash_screen=splash_screen)
            console.print()
            message_part = MessagePart(content_type="application/json", content=json.dumps({"steps": workflow_steps}))
            async with acp_client() as client:
                await _run_agent(
                    client, name, [Message(parts=[message_part])], dump_files_path=dump_files, handle_input=handle_input
                )

    else:
        async with acp_client() as client:
            await _run_agent(client, name, input, dump_files_path=dump_files)


def render_enum(value: str, colors: dict[str, str]) -> str:
    if color := colors.get(value):
        return f"[{color}]{value}[/{color}]"
    return value


def _get_short_location(provider_id: str) -> str:
    return re.sub(r"[a-z]*.io/i-am-bee/beeai-platform/", "", provider_id)


@app.command("list")
async def list_agents():
    """List agents."""
    agents = await _get_agents()
    providers_by_id = {p["id"]: p for p in (await api_request("GET", "providers"))["items"]}
    max_provider_len = (
        max(len(_get_short_location(p["source"])) for p in providers_by_id.values()) if providers_by_id else 0
    )

    def _sort_fn(agent: Agent):
        if not (provider := providers_by_id.get(agent.metadata.provider_id)):
            return agent.name
        state = {"missing": "1"}
        return str(state.get(provider["state"], 0)) + f"_{agent.name}" if "registry" in provider else agent.name

    with create_table(
        Column("Name", style="yellow"),
        Column("State", width=len("starting")),
        Column("Description", max_width=30),
        Column("UI"),
        Column("Location", max_width=min(max_provider_len, 70)),
        Column("Missing Env", max_width=50),
        Column("Last Error", ratio=1),
        no_wrap=True,
    ) as table:
        for agent in sorted(agents.values(), key=_sort_fn):
            state = None
            missing_env = None
            location = None
            error = None
            if provider := providers_by_id.get(agent.metadata.provider_id, None):
                state = provider["state"]
                missing_env = ",".join(var["name"] for var in provider["missing_configuration"])
                location = _get_short_location(provider["source"])
                error = (
                    (provider.get("last_error") or {}).get("message", None)
                    if provider["state"] != "ready"
                    else "<none>"
                )
            table.add_row(
                agent.name,
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
                (agent.description or "<none>").replace("\n", " "),
                (agent.metadata.model_dump().get("ui", {}) or {}).get("type", None) or "<none>",
                location or "<none>",
                missing_env or "<none>",
                error or "<none>",
            )
    console.print(table)


async def _get_agents() -> dict[str, Agent]:
    async with acp_client() as client:
        agents: list[Agent] = [agent async for agent in client.agents()]
    agents_by_name = {agent.name: agent for agent in agents}
    return agents_by_name


async def _get_agent(name: str, agents_by_name: dict[str, Agent] | None = None) -> Agent:
    if not agents_by_name:
        agents_by_name = await _get_agents()
    if agent := agents_by_name.get(name, None):
        return agent
    raise ACPError(error=Error(code=ErrorCode.NOT_FOUND, message=f"Agent '{name}' not found"))


def _render_schema(schema: dict[str, Any] | None):
    return "No schema provided." if not schema else rich.json.JSON.from_data(schema)


def _render_examples(agent: Agent):
    if not (examples := (agent.metadata.model_dump().get("examples", {}) or {}).get("cli", []) or []):
        return Text()
    md = "## Examples"
    for i, example in enumerate(examples):
        processing_steps = "\n".join(
            f"{i + 1}. {step}" for i, step in enumerate(example.get("processing_steps", []) or [])
        )
        name = example.get("name", None) or f"Example #{i + 1}"
        output = f"""
### Output
```
{example.get("output", "")}
```
"""
        md += f"""
### {name}
{example.get("description", None) or ""}

#### Command
```sh
{example["command"]}
```
{output if example.get("output", None) else ""}

#### Processing steps
{processing_steps}
"""

    return Markdown(md)


@app.command("info")
async def agent_detail(name: typing.Annotated[str, typer.Argument(help="Name of agent tool to show")]):
    """Show agent details."""
    agent = await _get_agent(name)

    basic_info = f"# {agent.name}\n{agent.description}"

    console.print(Markdown(basic_info), "")
    console.print(Markdown(agent.metadata.documentation or ""))
    console.print(_render_examples(agent))

    with create_table(Column("Key", ratio=1), Column("Value", ratio=5), title="Extra information") as table:
        for key, value in omit(agent.metadata.model_dump(), {"documentation", "examples"}).items():
            if value:
                table.add_row(key, str(value))
    console.print()
    console.print(table)

    provider = await get_provider(agent.metadata.provider_id)
    with create_table(Column("Key", ratio=1), Column("Value", ratio=5), title="Provider") as table:
        for key, value in omit(provider, {"image_id", "manifest", "source", "registry"}).items():
            table.add_row(key, str(value))
    console.print()
    console.print(table)
