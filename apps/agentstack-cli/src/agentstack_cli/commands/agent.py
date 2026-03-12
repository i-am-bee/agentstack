# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import asyncio
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
    CheckboxGroupField,
    CheckboxGroupFieldValue,
    DateField,
    DateFieldValue,
    FormFieldValue,
    FormRender,
    FormResponse,
    MultiSelectField,
    MultiSelectFieldValue,
    SettingsFormFieldValue,
    SettingsFormRender,
    SettingsFormResponse,
    SingleSelectField,
    SingleSelectFieldValue,
    TextField,
    TextFieldValue,
)

# Legacy settings extension (deprecated - use FormServiceExtensionSpec.demand_settings instead)
from agentstack_sdk.a2a.extensions.ui.settings import (
    AgentRunSettings,
    SettingsExtensionSpec,
    SettingsFieldValue,
    SettingsRender,
)
from agentstack_sdk.a2a.extensions.ui.settings import (
    CheckboxFieldValue as SettingsCheckboxFieldValue,
)
from agentstack_sdk.a2a.extensions.ui.settings import (
    CheckboxGroupField as SettingsCheckboxGroupField,
)
from agentstack_sdk.a2a.extensions.ui.settings import (
    CheckboxGroupFieldValue as SettingsCheckboxGroupFieldValue,
)
from agentstack_sdk.a2a.extensions.ui.settings import (
    SingleSelectField as SettingsSingleSelectField,
)
from agentstack_sdk.a2a.extensions.ui.settings import (
    SingleSelectFieldValue as SettingsSingleSelectFieldValue,
)
from agentstack_sdk.platform import File, ModelProvider, Provider, UserFeedback
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

from agentstack_cli.commands.model import ensure_llm_provider
from agentstack_cli.configuration import Configuration

# This is necessary for proper handling of arrow keys in interactive input
if sys.platform != "win32":
    import importlib

    try:
        readline = importlib.import_module("gnureadline")
    except ImportError:
        readline = importlib.import_module("readline")

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
from agentstack_cli.server_utils import announce_server_action, confirm_server_action
from agentstack_cli.utils import (
    generate_schema_example,
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
    "Asking agents...",
    "Booting up bots...",
    "Calibrating cognition...",
    "Directing drones...",
    "Engaging engines...",
    "Fetching functions...",
    "Gathering goals...",
    "Hardening hypotheses...",
    "Interpreting intentions...",
    "Juggling judgements...",
    "Kernelizing knowledge...",
    "Loading logic...",
    "Mobilizing models...",
    "Nudging networks...",
    "Optimizing outputs...",
    "Prompting pipelines...",
    "Quantizing queries...",
    "Refining responses...",
    "Scaling stacks...",
    "Tuning transformers...",
    "Unifying understandings...",
    "Vectorizing values...",
    "Wiring workflows...",
    "Xecuting xperiments...",
    "Yanking YAMLs...",
    "Zipping zettabytes...",
]

configuration = Configuration()


async def _discover_agent_card(location: str) -> AgentCard:
    """Fetch agent card from a network URL's well-known endpoint."""
    from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH

    url = location.rstrip("/") + AGENT_CARD_WELL_KNOWN_PATH
    console.info(f"Fetching agent card from {url}...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        return AgentCard.model_validate(resp.json())


@app.command("add")
async def add_agent(
    location: typing.Annotated[
        str | None, typer.Argument(help="Agent image or network URL")
    ] = None,
    name: typing.Annotated[str | None, typer.Option("--name", "-n", help="Agent name (default: derived from image)")] = None,
    namespace: typing.Annotated[str, typer.Option(help="Target Kubernetes namespace")] = "team1",
    port: typing.Annotated[int, typer.Option(help="Agent service port")] = 8080,
    env: typing.Annotated[list[str] | None, typer.Option("--env", "-e", help="Environment variable in KEY=VALUE format (repeatable)")] = None,
    env_file: typing.Annotated[str | None, typer.Option("--env-file", help="Path to env file (KEY=VALUE per line)")] = None,
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
) -> None:
    """Add an agent by container image or network URL. [Admin only]"""
    if location is None:
        location = (
            await inquirer.text(
                message="Enter agent image or URL:",
            ).execute_async()
            or ""
        )

    if not location:
        console.error("No location provided. Exiting.")
        sys.exit(1)

    url = announce_server_action(f"Installing agent '{location}' for")
    await confirm_server_action("Proceed with installing this agent on", url=url, yes=yes)

    # Detect if location is a container image (contains registry address or no protocol)
    is_image = not location.startswith("http://") and not location.startswith("https://")

    if is_image:
        await _add_agent_via_kagenti(location, name=name, namespace=namespace, port=port, env=env, env_file=env_file)
    else:
        # Legacy path: register network URL directly with agentstack
        try:
            with status("Registering agent to platform"):
                async with configuration.use_platform_client():
                    await Provider.create(location=location)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                agent_card = await _discover_agent_card(location)
                with status("Registering agent with discovered card"):
                    async with configuration.use_platform_client():
                        await Provider.create(location=location, agent_card=agent_card)
            else:
                raise
        console.success(f"Agent [bold]{location}[/bold] added to platform")
    await list_agents()


async def _add_agent_via_kagenti(
    image: str,
    *,
    name: str | None,
    namespace: str,
    port: int,
    env: list[str] | None = None,
    env_file: str | None = None,
) -> None:
    """Deploy a pre-built image via kagenti and wait for it to become healthy."""
    import asyncio
    import contextlib
    import re

    from agentstack_cli.kagenti_client import KagentiClient

    # Derive name from image if not provided
    if not name:
        # Extract last path component, strip tag/digest
        raw = image.rsplit("/", 1)[-1].split(":")[0].split("@")[0]
        name = re.sub(r"[^a-z0-9-]", "-", raw.lower()).strip("-")[:63] or "agent"

    # Get auth token
    auth_token = None
    try:
        auth_token = await configuration.auth_manager.load_auth_token()
    except Exception:
        if configuration.auth_manager.active_server and "agentstack-api.localtest.me" in configuration.auth_manager.active_server:
            with contextlib.suppress(Exception):
                auth_token = await configuration.auth_manager.login_with_password(
                    configuration.auth_manager.active_server, username="admin", password="admin"
                )

    if not auth_token:
        console.error("Not authenticated. Run [green]agentstack server login[/green] first.")
        sys.exit(1)

    client = KagentiClient(configuration.kagenti_url, auth_token.access_token)

    # Build env vars: start with defaults, then merge user-provided ones
    env_vars: dict[str, str] = {
        "PORT": "8000",
        "HOST": "0.0.0.0",
        "PLATFORM_URL": "http://agentstack-server-svc.agentstack:8333",
        "PLATFORM_AUTH__SKIP_AUDIENCE_VALIDATION": "true",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector.kagenti-system:8335",
    }

    # Parse --env-file (KEY=VALUE per line, ignoring comments and blank lines)
    if env_file:
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, _, value = line.partition("=")
                    if key:
                        env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            console.error(f"Env file not found: {env_file}")
            sys.exit(1)

    # Parse --env KEY=VALUE flags (override env-file and defaults)
    if env:
        for entry in env:
            key, _, value = entry.partition("=")
            if not key or not _:
                console.error(f"Invalid env format '{entry}', expected KEY=VALUE")
                sys.exit(1)
            env_vars[key] = value

    # Create agent in kagenti
    request = {
        "name": name,
        "namespace": namespace,
        "deploymentMethod": "image",
        "containerImage": image,
        "workloadType": "deployment",
        "servicePorts": [{"port": port, "protocol": "TCP"}],
        "envVars": [{"name": k, "value": v} for k, v in env_vars.items()],
    }

    try:
        with status(f"Deploying agent '{name}' via kagenti"):
            await client.create_agent(request)
    except httpx.ConnectError:
        console.error(f"Cannot connect to kagenti at [cyan]{configuration.kagenti_url}[/cyan]")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        detail = ""
        with contextlib.suppress(Exception):
            detail = e.response.json().get("detail", "")
        console.error(f"Failed to create agent: {e.response.status_code} {detail or e.response.text}")
        sys.exit(1)

    console.success(f"Agent [bold]{name}[/bold] submitted to kagenti")

    # Poll kagenti for agent health (60s timeout)
    console.info("Waiting for agent to become healthy in kagenti...")
    healthy = False
    for _ in range(60):
        await asyncio.sleep(1)
        try:
            agent = await client.get_agent(namespace, name)
            ready_status = agent.get("readyStatus", "")
            if ready_status.lower() in ("running", "ready", "healthy"):
                healthy = True
                break
        except Exception:
            pass

    if not healthy:
        console.warning(
            f"Agent [bold]{name}[/bold] did not become healthy within 60s. "
            f"Check kagenti UI or [green]kubectl get pods -n {namespace}[/green] for details."
        )
    else:
        console.success(f"Agent [bold]{name}[/bold] is healthy in kagenti")

    # Wait for agent to appear in agentstack (30s timeout)
    console.info("Waiting for agent to appear in agentstack...")
    appeared = False
    for _ in range(30):
        await asyncio.sleep(1)
        try:
            async with configuration.use_platform_client():
                providers = await Provider.list()
                if any(name in (p.agent_card.name or "") or name in (p.origin or "") for p in providers):
                    appeared = True
                    break
        except Exception:
            pass

    if not appeared:
        console.warning(
            f"Agent [bold]{name}[/bold] has not appeared in agentstack within 30s. "
            "It may take longer for kagenti to sync the agent."
        )


@app.command("update")
async def update_agent(
    search_path: typing.Annotated[
        str | None, typer.Argument(help="Short ID, agent name or part of the provider location of agent to replace")
    ] = None,
    location: typing.Annotated[
        str | None, typer.Argument(help="New agent location (network URL)")
    ] = None,
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
) -> None:
    """Update an agent's location. [Admin only]"""
    async with configuration.use_platform_client():
        providers = await Provider.list()

    if search_path is None:
        if not providers:
            console.error("No agents found. Add an agent first using 'agentstack agent add'.")
            sys.exit(1)

        provider_choices = [
            Choice(value=p, name=f"{p.agent_card.name} ({ProviderUtils.short_location(p)})") for p in providers
        ]
        provider = await inquirer.fuzzy(
            message="Select an agent to update:",
            choices=provider_choices,
        ).execute_async()
        if not provider:
            console.error("No agent selected. Exiting.")
            sys.exit(1)
    else:
        provider = select_provider(search_path, providers=providers)

    if location is None:
        location = (
            await inquirer.text(
                message="Enter new agent location (URL):",
                default=provider.origin,
            ).execute_async()
            or ""
        )

    if not location:
        console.error("No location provided. Exiting.")
        sys.exit(1)

    url = announce_server_action(f"Upgrading agent from '{provider.origin}' to {location}")
    await confirm_server_action("Proceed with upgrading agent on", url=url, yes=yes)

    with status("Upgrading agent in the platform"):
        async with configuration.use_platform_client():
            await provider.patch(location=location)
    console.success(f"Agent [bold]{location}[/bold] updated on platform")
    await list_agents()


def search_path_match_providers(search_path: str, providers: list[Provider]) -> dict[str, Provider]:
    search_path = search_path.lower()
    return {
        p.id: p
        for p in providers
        if (
            search_path in p.id.lower()
            or search_path in p.agent_card.name.lower()
            or search_path in ProviderUtils.short_location(p)
        )
    }


def select_provider(search_path: str, providers: list[Provider]):
    provider_candidates = search_path_match_providers(search_path, providers)
    if len(provider_candidates) == 0:
        raise ValueError(f"No agents matched '{search_path}'")
    if len(provider_candidates) > 1:
        candidates_detail = "\n".join(f"  - {c}" for c in provider_candidates)
        raise ValueError(f"Multiple agents matched '{search_path}':\n{candidates_detail}")
    [selected_provider] = provider_candidates.values()
    return selected_provider


async def select_providers_multi(search_path: str, providers: list[Provider]) -> list[Provider]:
    """Select multiple providers matching the search path."""
    provider_candidates = search_path_match_providers(search_path, providers)
    if not provider_candidates:
        raise ValueError(f"No matching agents found for '{search_path}'")

    if len(provider_candidates) == 1:
        return list(provider_candidates.values())

    # Multiple matches - show selection menu
    choices = [Choice(value=p.id, name=f"{p.agent_card.name} - {p.id}") for p in provider_candidates.values()]

    selected_ids = await inquirer.checkbox(
        message="Select agents to remove (use ↑/↓ to navigate, Space to select):",
        choices=choices,
        validate=lambda result: len(result) > 0,
        invalid_message="Please select at least one agent using Space before pressing Enter.",
    ).execute_async()

    return [provider_candidates[pid] for pid in (selected_ids or [])]


@app.command("remove | uninstall | rm | delete")
async def uninstall_agent(
    search_path: typing.Annotated[
        str, typer.Argument(help="Short ID, agent name or part of the provider location")
    ] = "",
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
    all: typing.Annotated[bool, typer.Option("--all", "-a", help="Remove all agents without selection.")] = False,
) -> None:
    """Remove agent. [Admin only]"""
    if search_path and all:
        console.error(
            "[bold]Cannot specify both --all and a search path."
            " Use --all to remove all agents, or provide a search path for specific agents."
            "[/bold]"
        )
        raise typer.Exit(1)

    async with configuration.use_platform_client():
        providers = await Provider.list()
        if len(providers) == 0:
            console.info("No agents found to remove.")
            return

        if all:
            selected_providers = providers
        else:
            selected_providers = await select_providers_multi(search_path, providers)
        if not selected_providers:
            console.info("No agents selected for removal, exiting.")
            return
        elif len(selected_providers) == 1:
            agent_names = f"{selected_providers[0].agent_card.name} - {selected_providers[0].id.split('-', 1)[0]}"
        else:
            agent_names = "\n".join([f"  - {p.agent_card.name} - {p.id.split('-', 1)[0]}" for p in selected_providers])

        message = f"\n[bold]Selected agents to remove:[/bold]\n{agent_names}\n from "

        url = announce_server_action(message)
        await confirm_server_action("Proceed with removing these agents from", url=url, yes=yes)

        with console.status("Uninstalling agent(s) (may take a few minutes)...", spinner="dots"):
            delete_tasks = [Provider.delete(provider.id) for provider in selected_providers]
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)

        # Check results for exceptions
        for provider, result in zip(selected_providers, results, strict=True):
            if isinstance(result, Exception):
                err_console.print(f"Failed to delete {provider.agent_card.name}: {result}")
            # else: deletion succeeded

        # Also delete kagenti-sourced agents from kagenti
        kagenti_providers = [p for p in selected_providers if p.source_type == "kagenti" and p.origin]
        if kagenti_providers:
            import contextlib
            from urllib.parse import urlparse

            from agentstack_cli.kagenti_client import KagentiClient

            auth_token = None
            try:
                auth_token = await configuration.auth_manager.load_auth_token()
            except Exception:
                if configuration.auth_manager.active_server and "agentstack-api.localtest.me" in configuration.auth_manager.active_server:
                    with contextlib.suppress(Exception):
                        auth_token = await configuration.auth_manager.login_with_password(
                            configuration.auth_manager.active_server, username="admin", password="admin"
                        )

            if auth_token:
                client = KagentiClient(configuration.kagenti_url, auth_token.access_token)
                for provider in kagenti_providers:
                    # Parse name and namespace from origin URL: http://{name}.{namespace}.svc.cluster.local:8080
                    parsed = urlparse(provider.origin)
                    host_parts = (parsed.hostname or "").split(".")
                    if len(host_parts) >= 2:
                        agent_name, namespace = host_parts[0], host_parts[1]
                        try:
                            await client.delete_agent(namespace, agent_name)
                            console.success(f"Deleted [bold]{agent_name}[/bold] from kagenti")
                        except Exception as ex:
                            err_console.print(f"Failed to delete {agent_name} from kagenti: {ex}")
            else:
                err_console.print("Could not authenticate to kagenti — agents may reappear via sync.")

    await list_agents()


async def _ask_form_questions(form_render: FormRender) -> FormResponse:
    """Ask user to fill a form using inquirer."""
    form_values: dict[str, FormFieldValue] = {}

    console.print("[bold]Form input[/bold]" + (f": {form_render.title}" if form_render.title else ""))
    if form_render.description:
        console.print(f"{form_render.description}\n")

    for field in form_render.fields:
        if isinstance(field, TextField):
            answer = await inquirer.text(
                message=field.label + ":",
                default=field.default_value or "",
                validate=EmptyInputValidator() if field.required else None,
            ).execute_async()
            form_values[field.id] = TextFieldValue(value=answer)
        elif isinstance(field, SingleSelectField):
            choices = [Choice(value=opt.id, name=opt.label) for opt in field.options]
            answer = await inquirer.fuzzy(
                message=field.label + ":",
                choices=choices,
                default=field.default_value,
                validate=EmptyInputValidator() if field.required else None,
            ).execute_async()
            form_values[field.id] = SingleSelectFieldValue(value=answer)
        elif isinstance(field, MultiSelectField):
            choices = [Choice(value=opt.id, name=opt.label) for opt in field.options]
            answer = await inquirer.checkbox(
                message=field.label + ":",
                choices=choices,
                default=field.default_value,
                validate=EmptyInputValidator() if field.required else None,
            ).execute_async()
            form_values[field.id] = MultiSelectFieldValue(value=answer)

        elif isinstance(field, DateField):
            year = await inquirer.text(
                message=f"{field.label} (year):",
                validate=EmptyInputValidator() if field.required else None,
                filter=lambda y: y.strip(),
            ).execute_async()
            if not year:
                continue
            month = await inquirer.fuzzy(
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
            day = await inquirer.fuzzy(
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
            answer = await inquirer.confirm(
                message=field.label + ":",
                default=field.default_value,
                long_instruction=field.content or "",
            ).execute_async()
            form_values[field.id] = CheckboxFieldValue(value=answer)
    console.print()
    return FormResponse(values=form_values)


# TODO: remove once legacy settings extension is fully deprecated
async def _ask_settings_questions(settings_render: SettingsRender) -> AgentRunSettings:
    """Ask user to configure settings using inquirer."""
    settings_values: dict[str, SettingsFieldValue] = {}

    console.print("[bold]Agent Settings[/bold]\n")
    for field in settings_render.fields:
        if isinstance(field, SettingsCheckboxGroupField):
            checkbox_values: dict[str, SettingsCheckboxFieldValue] = {}
            for checkbox in field.fields:
                answer = await inquirer.confirm(
                    message=checkbox.label + ":",
                    default=checkbox.default_value,
                ).execute_async()
                checkbox_values[checkbox.id] = SettingsCheckboxFieldValue(value=answer)
            settings_values[field.id] = SettingsCheckboxGroupFieldValue(values=checkbox_values)
        elif isinstance(field, SettingsSingleSelectField):
            choices = [Choice(value=opt.value, name=opt.label) for opt in field.options]
            answer = await inquirer.fuzzy(
                message=field.label + ":",
                choices=choices,
                default=field.default_value,
            ).execute_async()
            settings_values[field.id] = SettingsSingleSelectFieldValue(value=answer)
        else:
            raise ValueError(f"Unsupported settings field type: {type(field).__name__}")

    console.print()
    return AgentRunSettings(values=settings_values)


async def _ask_settings_form_questions(settings_render: SettingsFormRender) -> SettingsFormResponse:
    """Ask user to configure settings using the new form extension format."""
    settings_values: dict[str, SettingsFormFieldValue] = {}

    console.print("[bold]Agent Settings[/bold]\n")

    for field in settings_render.fields:
        if isinstance(field, CheckboxGroupField):
            checkbox_value: dict[str, bool | None] = {}
            for checkbox in field.fields:
                answer = await inquirer.confirm(
                    message=checkbox.label + ":",
                    default=checkbox.default_value,
                ).execute_async()
                checkbox_value[checkbox.id] = answer
            settings_values[field.id] = CheckboxGroupFieldValue(value=checkbox_value)
        elif isinstance(field, SingleSelectField):
            choices = [Choice(value=opt.id, name=opt.label) for opt in field.options]
            answer = await inquirer.fuzzy(
                message=field.label + ":",
                choices=choices,
                default=field.default_value,
            ).execute_async()
            settings_values[field.id] = SingleSelectFieldValue(value=answer)
        else:
            raise ValueError(f"Unsupported settings field type: {type(field).__name__}")

    console.print()
    return SettingsFormResponse(values=settings_values)


# TODO: adjust or remove the following function once legacy settings extension is fully deprecated and all agents have transitioned to the new form-based settings extension
def _get_settings_from_agent_card(agent_card: AgentCard) -> tuple[SettingsFormRender | SettingsRender | None, bool]:
    """
    Extract settings from agent card, supporting both legacy and new format.

    Returns:
        Tuple of (settings_render, is_legacy) where:
        - settings_render: The settings form render (SettingsFormRender for new, SettingsRender for legacy, or None)
        - is_legacy: True if using old settings extension, False if using new form extension

    """
    # Try new format first (form extension with settings_form)
    form_spec = FormServiceExtensionSpec.from_agent_card(agent_card)
    if form_spec and form_spec.params:
        settings_form = form_spec.params.form_demands.get("settings_form")
        if settings_form:
            return settings_form, False

    # Fall back to legacy settings extension - return original SettingsRender
    # The fields will use legacy types with type="single_select" and type="checkbox_group"
    settings_spec = SettingsExtensionSpec.from_agent_card(agent_card)
    if settings_spec and settings_spec.params:
        return settings_spec.params, True

    return None, False


async def _run_agent(
    client: Client,
    input: str | DataPart | FormResponse,
    agent_card: AgentCard,
    context_token: ContextToken,
    settings: AgentRunSettings | SettingsFormResponse | None = None,
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
                        "form_fulfillments": {
                            **(
                                {"initial_form": input.model_dump(mode="json")}
                                if isinstance(input, FormResponse)
                                else {}
                            ),
                            **(
                                {"settings_form": settings.model_dump(mode="json")}
                                if isinstance(settings, SettingsFormResponse)
                                else {}
                            ),
                        }
                    }
                }
                if isinstance(input, FormResponse) or isinstance(settings, SettingsFormResponse)
                else {}
            )
            | (
                PlatformApiExtensionClient(platform_extension_spec).api_auth_metadata(
                    auth_token=context_token.token, expires_at=context_token.expires_at
                )
                if platform_extension_spec
                else {}
            )
            | (  # TODO: remove once legacy settings extension is fully deprecated
                # Ensure legacy settings use the correct field types (single_select, checkbox_group)
                # by explicitly serializing with mode="json"
                {SettingsExtensionSpec.URI: settings.model_dump(mode="json")}
                if isinstance(settings, AgentRunSettings)
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
                    status=TaskStatus(state=TaskState.working | TaskState.submitted, message=message)
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
                    dump_files_path.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240
                    full_path = dump_files_path / (artifact.name or "unnamed").lstrip("/")
                    full_path.resolve().relative_to(dump_files_path.resolve())  # noqa: ASYNC240
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
                    # pyrefly: ignore [bad-argument-type] -- probably a bug in Pyrefly
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
    async with configuration.use_platform_client():
        providers = await Provider.list()
        await ensure_llm_provider()

        if search_path is None:
            if not providers:
                err_console.error("No agents found. Add an agent first using 'agentstack agent add'.")
                sys.exit(1)
            search_path = await inquirer.fuzzy(
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

    # Extract settings from agent card (supports both legacy and new format)
    settings_render, is_legacy_settings = _get_settings_from_agent_card(agent)

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
                if ext.uri == FormServiceExtensionSpec.URI
                and ext.params
                and ext.params.get("form_demands", {}).get("initial_form")
            ),
            None,
        )
        if interaction_mode == InteractionMode.MULTI_TURN:
            console.print(f"{user_greeting}\n")
            # Ask settings based on format (legacy or new)
            settings_input: AgentRunSettings | SettingsFormResponse | None = None
            if settings_render:
                # TODO: remove once legacy settings extension is fully deprecated
                if is_legacy_settings:
                    settings_input = await _ask_settings_questions(settings_render)  # type: ignore
                else:
                    settings_input = await _ask_settings_form_questions(settings_render)  # type: ignore

            turn_input = await _ask_form_questions(initial_form_render) if initial_form_render else handle_input()
            async with a2a_client(provider.agent_card, context_token=context_token) as client:
                while True:
                    console.print()
                    await _run_agent(
                        client,
                        input=turn_input,
                        agent_card=agent,
                        context_token=context_token,
                        settings=settings_input,
                        dump_files_path=dump_files,
                        handle_input=handle_input,
                    )
                    console.print()
                    turn_input = handle_input()
        elif interaction_mode == InteractionMode.SINGLE_TURN:
            user_greeting = ui_annotations.get("user_greeting", None) or "Enter your instructions."
            console.print(f"{user_greeting}\n")

            # Ask settings based on format (legacy or new)
            settings_input: AgentRunSettings | SettingsFormResponse | None = None
            if settings_render:
                # TODO: remove once legacy settings extension is fully deprecated
                if is_legacy_settings:
                    settings_input = await _ask_settings_questions(settings_render)  # type: ignore
                else:
                    settings_input = await _ask_settings_form_questions(settings_render)  # type: ignore
            console.print()
            async with a2a_client(provider.agent_card, context_token=context_token) as client:
                await _run_agent(
                    client,
                    input=await _ask_form_questions(initial_form_render) if initial_form_render else handle_input(),
                    agent_card=agent,
                    context_token=context_token,
                    settings=settings_input,
                    dump_files_path=dump_files,
                    handle_input=handle_input,
                )

    else:
        # Ask settings based on format (legacy or new)
        settings_input: AgentRunSettings | SettingsFormResponse | None = None
        if settings_render:
            if is_legacy_settings:
                # TODO: remove once legacy settings extension is fully deprecated
                settings_input = await _ask_settings_questions(settings_render)  # type: ignore
            else:
                settings_input = await _ask_settings_form_questions(settings_render)  # type: ignore

        async with a2a_client(provider.agent_card, context_token=context_token) as client:
            await _run_agent(
                client,
                input,
                agent_card=agent,
                context_token=context_token,
                settings=settings_input,
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
        return provider.agent_card.name

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
                    else ""
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
        for key, value in provider.model_dump(exclude={"source"}).items():
            table.add_row(key, str(value))
    console.print()
    console.print(table)


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
    """List your agent feedback. [Admin only]"""

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
