# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc
import base64
import calendar
import inspect
import json
import random
import re
import sys
import typing
from enum import StrEnum
from textwrap import dedent
from uuid import uuid4

import httpx
from a2a.client import Client
from a2a.types import (
    AgentCard,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from agentstack_sdk.a2a.extensions import (
    EmbeddingFulfillment,
    EmbeddingServiceExtensionClient,
    EmbeddingServiceExtensionSpec,
    FormRequestExtensionSpec,
    FormServiceExtensionSpec,
    LLMFulfillment,
    LLMServiceExtensionClient,
    LLMServiceExtensionSpec,
    PlatformApiExtensionClient,
    PlatformApiExtensionSpec,
    TrajectoryExtensionClient,
    TrajectoryExtensionSpec,
)
from agentstack_sdk.a2a.extensions.common.form import (
    CheckboxField,
    CheckboxFieldValue,
    DateField,
    DateFieldValue,
    FormFieldValue,
    FormRender,
    FormResponse,
    MultiSelectField,
    MultiSelectFieldValue,
    SingleSelectField,
    SingleSelectFieldValue,
    TextField,
    TextFieldValue,
)
from agentstack_sdk.platform import BuildState, File, ModelProvider, Provider, UserFeedback
from agentstack_sdk.platform.context import Context, ContextPermissions, ContextToken, Permissions
from agentstack_sdk.platform.model_provider import ModelCapability
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator
from pydantic import BaseModel
from rich.box import HORIZONTALS
from rich.console import ConsoleRenderable, Group, NewLine
from rich.panel import Panel
from rich.text import Text

from agentstack_cli.commands.build import _server_side_build
from agentstack_cli.commands.model import ensure_llm_provider
from agentstack_cli.configuration import Configuration

if sys.platform != "win32":
    try:
        # This is necessary for proper handling of arrow keys in interactive input
        import gnureadline as readline
    except ImportError:
        import readline  # noqa: F401

from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema
import rich.json
import typer
from rich.markdown import Markdown
from rich.table import Column

from agentstack_cli.api import a2a_client
from agentstack_cli.async_typer import AsyncTyper, console, create_table, err_console
from agentstack_cli.utils import (
    announce_server_action,
    confirm_server_action,
    generate_schema_example,
    is_github_url,
    parse_env_var,
    print_log,
    prompt_user,
    remove_nullable,
    status,
    verbosity,
)


class InteractionMode(StrEnum):
    SINGLE_TURN = "single-turn"
    MULTI_TURN = "multi-turn"


class ProviderUtils(BaseModel):
    @staticmethod
    def detail(provider: Provider) -> dict[str, str] | None:
        ui_extension = [
            ext for ext in provider.agent_card.capabilities.extensions or [] if "ui/agent-detail" in ext.uri
        ]
        return ui_extension[0].params if ui_extension else None

    @staticmethod
    def last_error(provider: Provider) -> str | None:
        return provider.last_error.message if provider.last_error and provider.state != "ready" else None

    @staticmethod
    def short_location(provider: Provider) -> str:
        return re.sub(r"[a-z]*.io/i-am-bee/agentstack/", "", provider.source).lower()


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

configuration = Configuration()


@app.command("add")
async def add_agent(
    location: typing.Annotated[
        str | None, typer.Argument(help="Agent location (public docker image or github url)")
    ] = None,
    dockerfile: typing.Annotated[str | None, typer.Option(help="Use custom dockerfile path")] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
) -> None:
    """Add a docker image or GitHub repository [aliases: install]"""
    if location is None:
        repo_input = (
            await inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                message="Enter GitHub repository (owner/repo or full URL):",
            ).execute_async()
            or ""
        )

        match = re.search(r"^(?:(?:https?://)?(?:www\.)?github\.com/)?([^/]+)/([^/?&]+)", repo_input)
        if not match:
            raise ValueError(f"Invalid GitHub URL format: {repo_input}. Expected 'owner/repo' or a full GitHub URL.")

        owner, repo = match.group(1), match.group(2).removesuffix(".git")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/tags",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            tags = [tag["name"] for tag in response.json()] if response.status_code == 200 else []

        if tags:
            selected_tag = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                message="Select a tag to use:",
                choices=tags,
            ).execute_async()
        else:
            selected_tag = (
                await inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                    message="Enter tag to use:",
                ).execute_async()
                or "main"
            )

        location = f"https://github.com/{owner}/{repo}@{selected_tag}"

    url = announce_server_action(f"Installing agent '{location}' for")
    await confirm_server_action("Proceed with installing this agent on", url=url, yes=yes)
    with verbosity(verbose):
        if is_github_url(location):
            console.info(f"Assuming GitHub repository, attempting to build agent from [bold]{location}[/bold]")
            with status("Building agent"):
                build = await _server_side_build(location, dockerfile, add=True, verbose=verbose)
            if build.status != BuildState.COMPLETED:
                error = build.error_message or "see logs above for details"
                raise RuntimeError(f"Agent build failed: {error}")
        else:
            if dockerfile:
                raise ValueError("Dockerfile can be specified only if location is a GitHub url")
            console.info(f"Assuming public docker image or network address, attempting to add {location}")
            with status("Registering agent to platform"):
                async with configuration.use_platform_client():
                    await Provider.create(location=location)
        console.success(f"Agent [bold]{location}[/bold] added to platform")
        await list_agents()


@app.command("update")
async def update_agent(
    search_path: typing.Annotated[
        str | None, typer.Argument(help="Short ID, agent name or part of the provider location of agent to replace")
    ] = None,
    location: typing.Annotated[
        str | None, typer.Argument(help="Agent location (public docker image or github url)")
    ] = None,
    dockerfile: typing.Annotated[str | None, typer.Option(help="Use custom dockerfile path")] = None,
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
) -> None:
    """Upgrade agent to a newer docker image or build from GitHub repository"""
    with verbosity(verbose):
        async with configuration.use_platform_client():
            providers = await Provider.list()

        if search_path is None:
            if not providers:
                console.error("No agents found. Add an agent first using 'agentstack agent add'.")
                sys.exit(1)

            provider_choices = [
                Choice(value=p, name=f"{p.agent_card.name} ({ProviderUtils.short_location(p)})") for p in providers
            ]
            provider = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                message="Select an agent to update:",
                choices=provider_choices,
            ).execute_async()
            if not provider:
                console.error("No agent selected. Exiting.")
                sys.exit(1)
        else:
            provider = select_provider(search_path, providers=providers)

        if location is None and is_github_url(provider.source):
            match = re.search(r"^(?:(?:https?://)?(?:www\.)?github\.com/)?([^/]+)/([^/@?&]+)", provider.source)
            if match:
                owner, repo = match.group(1), match.group(2).removesuffix(".git")

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/tags",
                        headers={"Accept": "application/vnd.github.v3+json"},
                    )
                    tags = [tag["name"] for tag in response.json()] if response.status_code == 200 else []

                if tags:
                    selected_tag = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                        message="Select a new tag to use:",
                        choices=tags,
                    ).execute_async()
                    if selected_tag:
                        location = f"https://github.com/{owner}/{repo}@{selected_tag}"

        if location is None:
            location = (
                await inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                    message="Enter new agent location (public docker image or github url):",
                    default=provider.source,
                ).execute_async()
                or ""
            )

        if not location:
            console.error("No location provided. Exiting.")
            sys.exit(1)

        url = announce_server_action(f"Upgrading agent from '{provider.source}' to {location}")
        await confirm_server_action("Proceed with upgrading agent on", url=url, yes=yes)

        if is_github_url(location):
            console.info(f"Assuming GitHub repository, attempting to build agent from [bold]{location}[/bold]")
            with status("Building agent"):
                build = await _server_side_build(
                    github_url=location, dockerfile=dockerfile, replace=provider.id, verbose=verbose
                )
            if build.status != BuildState.COMPLETED:
                error = build.error_message or "see logs above for details"
                raise RuntimeError(f"Agent build failed: {error}")
        else:
            if dockerfile:
                raise ValueError("Dockerfile can be specified only if location is a GitHub url")
            console.info(f"Assuming public docker image or network address, attempting to add {location}")
            with status("Upgrading agent in the platform"):
                async with configuration.use_platform_client():
                    await provider.patch(location=location)
        console.success(f"Agent [bold]{location}[/bold] added to platform")
        await list_agents()


def select_provider(search_path: str, providers: list[Provider]):
    search_path = search_path.lower()
    provider_candidates = {p.id: p for p in providers if search_path in p.id.lower()}
    provider_candidates.update({p.id: p for p in providers if search_path in p.agent_card.name.lower()})
    provider_candidates.update({p.id: p for p in providers if search_path in ProviderUtils.short_location(p)})
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
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
) -> None:
    """Remove agent"""
    url = announce_server_action(f"Removing agent '{search_path}' from")
    await confirm_server_action("Proceed with removing this agent from", url=url, yes=yes)
    with console.status("Uninstalling agent (may take a few minutes)...", spinner="dots"):
        async with configuration.use_platform_client():
            remove_provider = select_provider(search_path, await Provider.list()).id
            await Provider.delete(remove_provider)
    await list_agents()


@app.command("logs")
async def stream_logs(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
):
    """Stream agent provider logs"""
    announce_server_action(f"Streaming logs for '{search_path}' from")
    async with configuration.use_platform_client():
        provider = select_provider(search_path, await Provider.list()).id
        async for message in Provider.stream_logs(provider):
            print_log(message, ansi_mode=True)


async def _ask_form_questions(form_render: FormRender) -> FormResponse:
    """Ask user to fill a form using inquirer."""
    form_values: dict[str, FormFieldValue] = {}

    console.print("[bold]Form input[/bold]" + (f": {form_render.title}" if form_render.title else ""))
    if form_render.description:
        console.print(f"{form_render.description}\n")

    for field in form_render.fields:
        if isinstance(field, TextField):
            answer = await inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                message=field.label + ":",
                default=field.default_value or "",
                validate=EmptyInputValidator() if field.required else None,
            ).execute_async()
            form_values[field.id] = TextFieldValue(value=answer)
        elif isinstance(field, SingleSelectField):
            choices = [Choice(value=opt.id, name=opt.label) for opt in field.options]
            answer = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                message=field.label + ":",
                choices=choices,
                default=field.default_value,
                validate=EmptyInputValidator() if field.required else None,
            ).execute_async()
            form_values[field.id] = SingleSelectFieldValue(value=answer)
        elif isinstance(field, MultiSelectField):
            choices = [Choice(value=opt.id, name=opt.label) for opt in field.options]
            answer = await inquirer.checkbox(  # pyright: ignore[reportPrivateImportUsage]
                message=field.label + ":",
                choices=choices,
                default=field.default_value,
                validate=EmptyInputValidator() if field.required else None,
            ).execute_async()
            form_values[field.id] = MultiSelectFieldValue(value=answer)

        elif isinstance(field, DateField):
            year = await inquirer.text(  # pyright: ignore[reportPrivateImportUsage]
                message=f"{field.label} (year):",
                validate=EmptyInputValidator() if field.required else None,
                filter=lambda y: y.strip(),
            ).execute_async()
            if not year:
                continue
            month = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                message=f"{field.label} (month):",
                validate=EmptyInputValidator() if field.required else None,
                choices=[
                    Choice(
                        value=str(i).zfill(2),
                        name=f"{i:02d} - {calendar.month_name[i]}",
                    )
                    for i in range(1, 13)
                ],
            ).execute_async()
            if not month:
                continue
            day = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                message=f"{field.label} (day):",
                validate=EmptyInputValidator() if field.required else None,
                choices=[
                    Choice(value=str(i).zfill(2), name=str(i).zfill(2))
                    for i in range(1, calendar.monthrange(int(year), int(month))[1] + 1)
                ],
            ).execute_async()
            if not day:
                continue
            full_date = f"{year}-{month}-{day}"
            form_values[field.id] = DateFieldValue(value=full_date)
        elif isinstance(field, CheckboxField):
            answer = await inquirer.confirm(  # pyright: ignore[reportPrivateImportUsage]
                message=field.label + ":",
                default=field.default_value,
                long_instruction=field.content or "",
            ).execute_async()
            form_values[field.id] = CheckboxFieldValue(value=answer)
    console.print()
    return FormResponse(values=form_values)


async def _run_agent(
    client: Client,
    input: str | DataPart | FormResponse,
    agent_card: AgentCard,
    context_token: ContextToken,
    dump_files_path: Path | None = None,
    handle_input: Callable[[], str] | None = None,
    task_id: str | None = None,
) -> None:
    console_status = console.status(random.choice(processing_messages), spinner="dots")
    console_status.start()
    console_status_stopped = False

    log_type = None

    trajectory_spec = TrajectoryExtensionSpec.from_agent_card(agent_card)
    trajectory_extension = TrajectoryExtensionClient(trajectory_spec) if trajectory_spec else None
    llm_spec = LLMServiceExtensionSpec.from_agent_card(agent_card)
    embedding_spec = EmbeddingServiceExtensionSpec.from_agent_card(agent_card)
    platform_extension_spec = PlatformApiExtensionSpec.from_agent_card(agent_card)

    async with configuration.use_platform_client():
        metadata = (
            (
                LLMServiceExtensionClient(llm_spec).fulfillment_metadata(
                    llm_fulfillments={
                        key: LLMFulfillment(
                            api_base="{platform_url}/api/v1/openai/",
                            api_key=context_token.token.get_secret_value(),
                            api_model=(
                                await ModelProvider.match(
                                    suggested_models=demand.suggested,
                                    capability=ModelCapability.LLM,
                                )
                            )[0].model_id,
                        )
                        for key, demand in llm_spec.params.llm_demands.items()
                    }
                )
                if llm_spec
                else {}
            )
            | (
                EmbeddingServiceExtensionClient(embedding_spec).fulfillment_metadata(
                    embedding_fulfillments={
                        key: EmbeddingFulfillment(
                            api_base="{platform_url}/api/v1/openai/",
                            api_key=context_token.token.get_secret_value(),
                            api_model=(
                                await ModelProvider.match(
                                    suggested_models=demand.suggested,
                                    capability=ModelCapability.EMBEDDING,
                                )
                            )[0].model_id,
                        )
                        for key, demand in embedding_spec.params.embedding_demands.items()
                    }
                )
                if embedding_spec
                else {}
            )
            | (
                {
                    FormServiceExtensionSpec.URI: {
                        "form_fulfillments": {"initial_form": typing.cast(FormResponse, input).model_dump(mode="json")}
                    }
                }
                if isinstance(input, FormResponse)
                else {}
            )
            | (
                PlatformApiExtensionClient(platform_extension_spec).api_auth_metadata(
                    auth_token=context_token.token, expires_at=context_token.expires_at
                )
                if platform_extension_spec
                else {}
            )
        )

    msg = Message(
        message_id=str(uuid4()),
        parts=[
            Part(
                root=TextPart(text=input)
                if isinstance(input, str)
                else TextPart(text="")
                if isinstance(input, FormResponse)
                else input
            )
        ],
        role=Role.user,
        task_id=task_id,
        context_id=context_token.context_id,
        metadata=metadata,
    )

    stream = client.send_message(msg)

    while True:
        async for event in stream:
            if not console_status_stopped:
                console_status_stopped = True
                console_status.stop()
            match event:
                case Message(task_id=task_id) as message:
                    console.print(
                        dedent(
                            """\
                            ⚠️  [yellow]Warning[/yellow]:
                            Receiving message event outside of task is not supported.
                            Please use agentstack-sdk for writing your agents or ensure you always create a task first
                            using TaskUpdater() from a2a SDK: see https://a2a-protocol.org/v0.3.0/topics/life-of-a-task
                            """
                        )
                    )
                    # Basic fallback
                    for part in message.parts:
                        if isinstance(part.root, TextPart):
                            console.print(part.root.text)
                case Task(id=task_id), TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.completed, message=message)
                ):
                    console.print()  # Add newline after completion
                    return
                case Task(id=task_id), TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.working, message=message)
                ):
                    # Handle streaming content during working state
                    if message:
                        if trajectory_extension and (trajectory := trajectory_extension.parse_server_metadata(message)):
                            if update_kind := trajectory.title:
                                if update_kind != log_type:
                                    if log_type is not None:
                                        err_console.print()
                                    err_console.print(f"{update_kind}: ", style="dim", end="")
                                    log_type = update_kind
                                err_console.print(trajectory.content or "", style="dim", end="")
                        else:
                            # This is regular message content
                            if log_type:
                                console.print()
                                log_type = None
                        for part in message.parts:
                            if isinstance(part.root, TextPart):
                                console.print(part.root.text, end="")
                case Task(id=task_id), TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.input_required, message=message)
                ):
                    if handle_input is None:
                        raise ValueError("Agent requires input but no input handler provided")

                    if form_metadata := (
                        message.metadata.get(FormRequestExtensionSpec.URI) if message and message.metadata else None
                    ):
                        stream = client.send_message(
                            Message(
                                message_id=str(uuid4()),
                                parts=[],
                                role=Role.user,
                                task_id=task_id,
                                context_id=context_token.context_id,
                                metadata={
                                    FormRequestExtensionSpec.URI: (
                                        await _ask_form_questions(FormRender.model_validate(form_metadata))
                                    ).model_dump(mode="json")
                                },
                            )
                        )
                        break

                    text = ""
                    for part in message.parts if message else []:
                        if isinstance(part.root, TextPart):
                            text = part.root.text
                    console.print(f"\n[bold]Agent requires your input[/bold]: {text}\n")
                    user_input = handle_input()
                    stream = client.send_message(
                        Message(
                            message_id=str(uuid4()),
                            parts=[Part(root=TextPart(text=user_input))],
                            role=Role.user,
                            task_id=task_id,
                            context_id=context_token.context_id,
                        )
                    )
                    break
                case Task(id=task_id), TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.canceled | TaskState.failed | TaskState.rejected as status,
                        message=message,
                    )
                ):
                    error = ""
                    if message and message.parts and isinstance(message.parts[0].root, TextPart):
                        error = message.parts[0].root.text
                    console.print(f"\n:boom: [red][bold]Task {status.value}[/bold][/red]")
                    console.print(Markdown(error))
                    return
                case Task(id=task_id), TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.auth_required, message=message)
                ):
                    console.print("[yellow]Authentication required[/yellow]")
                    return
                case Task(id=task_id), TaskStatusUpdateEvent(status=TaskStatus(state=state, message=message)):
                    console.print(f"[yellow]Unknown task status: {state}[/yellow]")

                case Task(id=task_id), TaskArtifactUpdateEvent(artifact=artifact):
                    if dump_files_path is None:
                        continue
                    dump_files_path.mkdir(parents=True, exist_ok=True)
                    full_path = dump_files_path / (artifact.name or "unnamed").lstrip("/")
                    full_path.resolve().relative_to(dump_files_path.resolve())
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        for part in artifact.parts[:1]:
                            match part.root:
                                case FilePart():
                                    match part.root.file:
                                        case FileWithBytes(bytes=bytes_str):
                                            full_path.write_bytes(base64.b64decode(bytes_str))
                                        case FileWithUri(uri=uri):
                                            if uri.startswith("agentstack://"):
                                                async with File.load_content(uri.removeprefix("agentstack://")) as file:
                                                    full_path.write_bytes(file.content)
                                            else:
                                                async with httpx.AsyncClient() as httpx_client:
                                                    full_path.write_bytes((await httpx_client.get(uri)).content)
                                    console.print(f"📁 Saved {full_path}")
                                case TextPart(text=text):
                                    full_path.write_text(text)
                                case _:
                                    console.print(f"⚠️ Artifact part {type(part).__name__} is not supported")
                        if len(artifact.parts) > 1:
                            console.print("⚠️ Artifact with more than 1 part are not supported.")
                    except ValueError:
                        console.print(f"⚠️ Skipping artifact {artifact.name} - outside dump directory")
        else:
            break  # Stream ended normally


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

    def handle(self, args_str: str | None = None):
        sys.exit(0)


class ShowConfig(InteractiveCommand):
    """Show available and currently set configuration options"""

    command = "show-config"

    def __init__(self, config_schema: dict[str, Any] | None, config: dict[str, Any]):
        self.config_schema = config_schema or {}
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(self.config_schema)

    def handle(self, args_str: str | None = None):
        with create_table(Column("Key", ratio=1), Column("Type", ratio=3), Column("Example", ratio=2)) as schema_table:
            for prop, schema in self.config_schema["properties"].items():
                required_schema = remove_nullable(schema)
                schema_table.add_row(
                    prop,
                    json.dumps(required_schema),
                    json.dumps(generate_schema_example(required_schema)),  # pyright: ignore [reportArgumentType]
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
        self.config_schema = config_schema or {}
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

    def handle(self, args_str: str | None = None):
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
) -> Callable[[], str]:
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

    def handler() -> str:
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


@app.command("run")
async def run_agent(
    search_path: typing.Annotated[
        str | None,
        typer.Argument(
            help="Short ID, agent name or part of the provider location",
        ),
    ] = None,
    input: typing.Annotated[
        str | None,
        typer.Argument(
            help="Agent input as text or JSON",
        ),
    ] = None,
    dump_files: typing.Annotated[
        Path | None, typer.Option(help="Folder path to save any files returned by the agent")
    ] = None,
) -> None:
    """Run an agent."""
    if search_path is not None and input is None and sys.stdin.isatty():
        input = sys.stdin.read()
    async with configuration.use_platform_client():
        providers = await Provider.list()
        await ensure_llm_provider()

        if search_path is None:
            if not providers:
                err_console.error("No agents found. Add an agent first using 'agentstack agent add'.")
                sys.exit(1)
            search_path = await inquirer.fuzzy(  # pyright: ignore[reportPrivateImportUsage]
                message="Select an agent to run:",
                choices=[provider.agent_card.name for provider in providers],
            ).execute_async()
            if search_path is None:
                err_console.error("No agent selected. Exiting.")
                sys.exit(1)

        announce_server_action(f"Running agent '{search_path}' on")
        provider = select_provider(search_path, providers=providers)

        context = await Context.create(
            provider_id=provider.id,
            # TODO: remove metadata after UI migration
            metadata={"provider_id": provider.id, "agent_name": provider.agent_card.name},
        )
        context_token = await context.generate_token(
            grant_global_permissions=Permissions(llm={"*"}, embeddings={"*"}, a2a_proxy={"*"}, providers={"read"}),
            grant_context_permissions=ContextPermissions(files={"*"}, vector_stores={"*"}, context_data={"*"}),
        )

    agent = provider.agent_card

    if provider.state == "missing":
        console.print("Starting provider (this might take a while)...")
    if provider.state not in {"ready", "running", "starting", "missing", "online", "offline"}:
        err_console.print(f":boom: Agent is not in a ready state: {provider.state}, {provider.last_error}\nRetrying...")

    ui_annotations = ProviderUtils.detail(provider) or {}
    interaction_mode = ui_annotations.get("interaction_mode")

    user_greeting = ui_annotations.get("user_greeting", None) or "How can I help you?"

    splash_screen = Group(Markdown(f"# {agent.name}  \n{agent.description}"), NewLine())
    handle_input = _create_input_handler([], splash_screen=splash_screen)

    if not input:
        if interaction_mode not in {InteractionMode.MULTI_TURN, InteractionMode.SINGLE_TURN}:
            err_console.error(
                f"Agent {agent.name} does not use any supported UIs.\n"
                + "Please use the agent according to the following examples and schema:"
            )
            err_console.print(_render_examples(agent))
            exit(1)

        initial_form_render = next(
            (
                FormRender.model_validate(ext.params["form_demands"]["initial_form"])
                for ext in agent.capabilities.extensions or ()
                if ext.uri == FormServiceExtensionSpec.URI and ext.params
            ),
            None,
        )

        if interaction_mode == InteractionMode.MULTI_TURN:
            console.print(f"{user_greeting}\n")
            turn_input = await _ask_form_questions(initial_form_render) if initial_form_render else handle_input()
            async with a2a_client(provider.agent_card) as client:
                while True:
                    console.print()
                    await _run_agent(
                        client,
                        input=turn_input,
                        agent_card=agent,
                        context_token=context_token,
                        dump_files_path=dump_files,
                        handle_input=handle_input,
                    )
                    console.print()
                    turn_input = handle_input()
        elif interaction_mode == InteractionMode.SINGLE_TURN:
            user_greeting = ui_annotations.get("user_greeting", None) or "Enter your instructions."
            console.print(f"{user_greeting}\n")
            console.print()
            async with a2a_client(provider.agent_card) as client:
                await _run_agent(
                    client,
                    input=await _ask_form_questions(initial_form_render) if initial_form_render else handle_input(),
                    agent_card=agent,
                    context_token=context_token,
                    dump_files_path=dump_files,
                    handle_input=handle_input,
                )

    else:
        async with a2a_client(provider.agent_card) as client:
            await _run_agent(
                client,
                input,
                agent_card=agent,
                context_token=context_token,
                dump_files_path=dump_files,
                handle_input=handle_input,
            )


@app.command("list")
async def list_agents():
    """List agents."""
    announce_server_action("Listing agents on")
    async with configuration.use_platform_client():
        providers = await Provider.list()
    max_provider_len = max(len(ProviderUtils.short_location(p)) for p in providers) if providers else 0

    def _sort_fn(provider: Provider):
        state = {"missing": "1"}
        return (
            str(state.get(provider.state, 0)) + f"_{provider.agent_card.name}"
            if provider.registry
            else provider.agent_card.name
        )

    with create_table(
        Column("Short ID", style="yellow"),
        Column("Name", style="yellow"),
        Column("State"),
        Column("Location", max_width=min(max(max_provider_len, len("Location")), 70)),
        Column("Info", ratio=2),
        no_wrap=True,
    ) as table:
        for provider in sorted(providers, key=_sort_fn):
            table.add_row(
                provider.id[:8],
                provider.agent_card.name,
                {
                    "running": "[green]▶ running[/green]",
                    "online": "[green]● connected[/green]",
                    "ready": "[green]● idle[/green]",
                    "starting": "[yellow]✱ starting[/yellow]",
                    "missing": "[bright_black]○ not started[/bright_black]",
                    "offline": "[bright_black]○ disconnected[/bright_black]",
                    "error": "[red]✘ error[/red]",
                }.get(provider.state, provider.state or "<unknown>"),
                ProviderUtils.short_location(provider) or "<none>",
                (
                    f"Error: {error}"
                    if provider.state == "error" and (error := ProviderUtils.last_error(provider))
                    else f"Missing ENV: {{{', '.join(missing_env)}}}"
                    if (missing_env := [var.name for var in provider.missing_configuration])
                    else "<none>"
                ),
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
    announce_server_action(f"Showing agent details for '{search_path}' on")
    async with configuration.use_platform_client():
        provider = select_provider(search_path, await Provider.list())
    agent = provider.agent_card

    basic_info = f"# {agent.name}\n{agent.description}"

    console.print(Markdown(basic_info), "")
    console.print(Markdown("## Skills"))
    console.print()
    for skill in agent.skills:
        console.print(Markdown(f"**{skill.name}**  \n{skill.description}"))

    console.print(_render_examples(agent))

    with create_table(Column("Key", ratio=1), Column("Value", ratio=5), title="Extra information") as table:
        for key, value in agent.model_dump(exclude={"description", "examples"}).items():
            if value:
                table.add_row(key, str(value))
    console.print()
    console.print(table)

    with create_table(Column("Key", ratio=1), Column("Value", ratio=5), title="Provider") as table:
        for key, value in provider.model_dump(exclude={"image_id", "manifest", "source", "registry"}).items():
            table.add_row(key, str(value))
    console.print()
    console.print(table)


env_app = AsyncTyper()
app.add_typer(env_app, name="env")


async def _list_env(provider: Provider):
    async with configuration.use_platform_client():
        variables = await provider.list_variables()
    with create_table(Column("name", style="yellow"), Column("value", ratio=1)) as table:
        for name, value in sorted(variables.items()):
            table.add_row(name, value)
    console.print(table)


@env_app.command("add")
async def add_env(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
    env: typing.Annotated[list[str], typer.Argument(help="Environment variables to pass to agent")],
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
) -> None:
    """Store environment variables"""
    url = announce_server_action(f"Adding environment variables for '{search_path}' on")
    await confirm_server_action("Apply these environment variable changes on", url=url, yes=yes)
    env_vars = dict(parse_env_var(var) for var in env)
    async with configuration.use_platform_client():
        provider = select_provider(search_path, await Provider.list())
        await provider.update_variables(variables=env_vars)
    await _list_env(provider)


@env_app.command("list")
async def list_env(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
):
    """List stored environment variables"""
    announce_server_action(f"Listing environment variables for '{search_path}' on")
    async with configuration.use_platform_client():
        provider = select_provider(search_path, await Provider.list())
    await _list_env(provider)


@env_app.command("remove")
async def remove_env(
    search_path: typing.Annotated[
        str, typer.Argument(..., help="Short ID, agent name or part of the provider location")
    ],
    env: typing.Annotated[list[str], typer.Argument(help="Environment variable(s) to remove")],
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
):
    url = announce_server_action(f"Removing environment variables from '{search_path}' on")
    await confirm_server_action("Remove the selected environment variables on", url=url, yes=yes)
    async with configuration.use_platform_client():
        provider = select_provider(search_path, await Provider.list())
        await provider.update_variables(variables=dict.fromkeys(env))
    await _list_env(provider)


feedback_app = AsyncTyper()
app.add_typer(feedback_app, name="feedback", help="Manage user feedback for your agents", no_args_is_help=True)


@feedback_app.command("list")
async def list_feedback(
    search_path: typing.Annotated[
        str | None, typer.Argument(help="Short ID, agent name or part of the provider location")
    ] = None,
    limit: typing.Annotated[int, typer.Option("--limit", help="Number of results per page [default: 50]")] = 50,
    after_cursor: typing.Annotated[str | None, typer.Option("--after", help="Cursor for pagination")] = None,
):
    """List your agent feedback"""

    announce_server_action("Listing feedback on")

    provider_id = None

    async with configuration.use_platform_client():
        if search_path:
            providers = await Provider.list()
            provider = select_provider(search_path, providers)
            provider_id = str(provider.id)

        response = await UserFeedback.list(
            provider_id=provider_id,
            limit=limit,
            after_cursor=after_cursor,
        )

    if not response.items:
        console.print("No feedback found.")
        return

    with create_table(
        Column("Rating", style="yellow", ratio=1),
        Column("Agent", style="cyan", ratio=2),
        Column("Task ID", style="dim", ratio=1),
        Column("Comment", ratio=3),
        Column("Tags", ratio=2),
        Column("Date", style="dim", ratio=1),
    ) as table:
        for item in response.items:
            rating_icon = "✓" if item.rating == 1 else "✗"
            agent_name = item.agent_name or str(item.provider_id)[:8]
            task_id_short = str(item.task_id)[:8]
            comment = item.comment or ""
            if len(comment) > 50:
                comment = comment[:50] + "..."
            tags = ", ".join(item.comment_tags or []) if item.comment_tags else "-"
            created_at = item.created_at.strftime("%Y-%m-%d")

            table.add_row(rating_icon, agent_name, task_id_short, comment, tags, created_at)

    console.print(table)
    console.print(f"Showing {len(response.items)} of {response.total_count} total feedback entries")
    if response.has_more and response.next_page_token:
        console.print(f"Use --after {response.next_page_token} to see more")
