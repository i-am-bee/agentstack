# SPDX-License-Identifier: Apache-2.0


import functools
import os
import re
import shutil
import sys
import typing
from datetime import datetime

import httpx
import typer
from beeai_sdk.platform import ModelCapability, ModelProvider, ModelProviderType, SystemConfiguration
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator
from rich.table import Column

from beeai_cli.api import openai_client
from beeai_cli.async_typer import AsyncTyper, console, create_table
from beeai_cli.configuration import Configuration
from beeai_cli.utils import run_command, verbosity

app = AsyncTyper()
configuration = Configuration()


class ModelProviderError(Exception): ...


@functools.cache
def _ollama_exe() -> str:
    for exe in ("ollama", "ollama.exe"):
        if shutil.which(exe):
            return exe
    raise RuntimeError("Ollama executable not found")


RECOMMENDED_LLM_MODELS = [
    f"{ModelProviderType.WATSONX}:ibm/granite-3-3-8b-instruct",
    f"{ModelProviderType.OPENAI}:gpt-4o",
    f"{ModelProviderType.ANTHROPIC}:claude-sonnet-4-20250514",
    f"{ModelProviderType.CEREBRAS}:llama-3.3-70b",
    f"{ModelProviderType.CHUTES}:deepseek-ai/DeepSeek-R1",
    f"{ModelProviderType.COHERE}:command-r-plus",
    f"{ModelProviderType.DEEPSEEK}:deepseek-reasoner",
    f"{ModelProviderType.GEMINI}:models/gemini-2.5-pro",
    f"{ModelProviderType.GITHUB}:openai/gpt-4o",
    f"{ModelProviderType.GROQ}:meta-llama/llama-4-maverick-17b-128e-instruct",
    f"{ModelProviderType.MISTRAL}:mistral-large-latest",
    f"{ModelProviderType.MOONSHOT}:kimi-latest",
    f"{ModelProviderType.NVIDIA}:deepseek-ai/deepseek-r1",
    f"{ModelProviderType.OLLAMA}:granite3.3:8b",
    f"{ModelProviderType.OPENROUTER}:deepseek/deepseek-r1-distill-llama-70b:free",
    f"{ModelProviderType.TOGETHER}:deepseek-ai/DeepSeek-R1",
]

RECOMMENDED_EMBEDDING_MODELS = [
    f"{ModelProviderType.WATSONX}:ibm/granite-embedding-278m-multilingual",
    f"{ModelProviderType.OPENAI}:text-embedding-3-small",
    f"{ModelProviderType.COHERE}:embed-multilingual-v3.0",
    f"{ModelProviderType.GEMINI}:models/gemini-embedding-001",
    f"{ModelProviderType.MISTRAL}:mistral-embed",
    f"{ModelProviderType.OLLAMA}:nomic-embed-text:latest",
    f"{ModelProviderType.VOYAGE}:voyage-3.5",
]

LLM_PROVIDERS = [
    Choice(
        name="Anthropic Claude".ljust(25),
        value=(ModelProviderType.ANTHROPIC, "Anthropic Claude", "https://api.anthropic.com/v1"),
    ),
    Choice(
        name="Cerebras".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.CEREBRAS, "Cerebras", "https://api.cerebras.ai/v1"),
    ),
    Choice(
        name="Chutes".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.CHUTES, "Chutes", "https://llm.chutes.ai/v1"),
    ),
    Choice(
        name="Cohere".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.COHERE, "Cohere", "https://api.cohere.ai/compatibility/v1"),
    ),
    Choice(name="DeepSeek", value=(ModelProviderType.DEEPSEEK, "DeepSeek", "https://api.deepseek.com/v1")),
    Choice(
        name="Google Gemini".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.GEMINI, "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
    ),
    Choice(
        name="GitHub Models".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.GITHUB, "GitHub Models", "https://models.github.ai/inference"),
    ),
    Choice(
        name="Groq".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.GROQ, "Groq", "https://api.groq.com/openai/v1"),
    ),
    Choice(name="IBM watsonx".ljust(25), value=(ModelProviderType.WATSONX, "IBM watsonx", None)),
    Choice(name="Jan".ljust(25) + "💻 local", value=(ModelProviderType.JAN, "Jan", "http://localhost:1337/v1")),
    Choice(
        name="Mistral".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.MISTRAL, "Mistral", "https://api.mistral.ai/v1"),
    ),
    Choice(
        name="Moonshot AI".ljust(25),
        value=(ModelProviderType.MOONSHOT, "Moonshot AI", "https://api.moonshot.ai/v1"),
    ),
    Choice(
        name="NVIDIA NIM".ljust(25),
        value=(ModelProviderType.NVIDIA, "NVIDIA NIM", "https://integrate.api.nvidia.com/v1"),
    ),
    Choice(
        name="Ollama".ljust(25) + "💻 local",
        value=(ModelProviderType.OLLAMA, "Ollama", "http://localhost:11434/v1"),
    ),
    Choice(
        name="OpenAI".ljust(25),
        value=(ModelProviderType.OPENAI, "OpenAI", "https://api.openai.com/v1"),
    ),
    Choice(
        name="OpenRouter".ljust(25) + "🆓 has some free models",
        value=(ModelProviderType.OPENROUTER, "OpenRouter", "https://openrouter.ai/api/v1"),
    ),
    Choice(
        name="Perplexity".ljust(25),
        value=(ModelProviderType.PERPLEXITY, "Perplexity", "https://api.perplexity.ai"),
    ),
    Choice(
        name="together.ai".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.TOGETHER, "together.ai", "https://api.together.xyz/v1"),
    ),
    Choice(
        name="Other (RITS, vLLM, ...)".ljust(25) + "🔧 provide API URL",
        value=(ModelProviderType.OTHER, "Other", None),
    ),
]

EMBEDDING_PROVIDERS = [
    Choice(
        name="Cohere".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.COHERE, "Cohere", "https://api.cohere.ai/compatibility/v1"),
    ),
    Choice(
        name="Google Gemini".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.GEMINI, "Gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
    ),
    Choice(
        name="IBM watsonx".ljust(25),
        value=(ModelProviderType.WATSONX, "IBM watsonx", None),
    ),
    Choice(
        name="Mistral".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.MISTRAL, "Mistral", "https://api.mistral.ai/v1"),
    ),
    Choice(
        name=ModelProviderType.OLLAMA.ljust(25) + "💻 local",
        value=(ModelProviderType.OLLAMA, "Ollama", "http://localhost:11434/v1"),
    ),
    Choice(
        name="OpenAI".ljust(25),
        value=(ModelProviderType.OPENAI, "OpenAI", "https://api.openai.com/v1"),
    ),
    Choice(
        name="Voyage".ljust(25),
        value=(ModelProviderType.VOYAGE, "Voyage", "https://api.voyageai.com/v1"),
    ),
    Choice(
        name="Other (vLLM, ...)".ljust(25) + "🔧 provide API URL",
        value=(ModelProviderType.OTHER, "Other", None),
    ),
]


async def _add_provider(capability: ModelCapability, use_true_localhost: bool = False) -> ModelProvider:
    provider_type: str
    provider_name: str
    base_url: str
    watsonx_project_id, watsonx_space_id = None, None
    choices = LLM_PROVIDERS if capability == ModelCapability.LLM else EMBEDDING_PROVIDERS
    provider_type, provider_name, base_url = await inquirer.fuzzy(  # type: ignore
        message=f"Select {capability} provider (type to search):", choices=choices
    ).execute_async()

    watsonx_project_or_space: str = ""
    watsonx_project_or_space_id: str = ""

    if provider_type == ModelProviderType.OTHER:
        base_url: str = await inquirer.text(  # type: ignore
            message="Enter the base URL of your API (OpenAI-compatible):",
            validate=lambda url: (url.startswith(("http://", "https://")) or "URL must start with http:// or https://"),  # type: ignore
            transformer=lambda url: url.rstrip("/"),
        ).execute_async()
        if re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm\.com/.*$", base_url):
            provider_type = ModelProviderType.RITS
            if not base_url.endswith("/v1"):
                base_url = base_url.removesuffix("/") + "/v1"

    if provider_type == ModelProviderType.WATSONX:
        region: str = await inquirer.select(  # type: ignore
            message="Select IBM Cloud region:",
            choices=[
                Choice(name="us-south", value="us-south"),
                Choice(name="ca-tor", value="ca-tor"),
                Choice(name="eu-gb", value="eu-gb"),
                Choice(name="eu-de", value="eu-de"),
                Choice(name="jp-tok", value="jp-tok"),
                Choice(name="au-syd", value="au-syd"),
            ],
        ).execute_async()
        base_url: str = f"""https://{region}.ml.cloud.ibm.com"""
        watsonx_project_or_space: str = await inquirer.select(  # type:ignore
            "Use a Project or a Space?", choices=["project", "space"]
        ).execute_async()
        if (
            not (watsonx_project_or_space_id := os.environ.get(f"WATSONX_{watsonx_project_or_space.upper()}_ID", ""))
            or not await inquirer.confirm(  # type:ignore
                message=f"Use the {watsonx_project_or_space} id from environment variable 'WATSONX_{watsonx_project_or_space.upper()}_ID'?",
                default=True,
            ).execute_async()
        ):
            watsonx_project_or_space_id = await inquirer.text(  # type:ignore
                message=f"Enter the {watsonx_project_or_space} id:"
            ).execute_async()

        watsonx_project_id = watsonx_project_or_space_id if watsonx_project_or_space == "project" else None
        watsonx_space_id = watsonx_project_or_space_id if watsonx_project_or_space == "space" else None

    if (api_key := os.environ.get(f"{provider_type.upper()}_API_KEY")) is None or not await inquirer.confirm(  # type: ignore
        message=f"Use the API key from environment variable '{provider_type.upper()}_API_KEY'?",
        default=True,
    ).execute_async():
        api_key: str = (
            "dummy"
            if provider_type in {ModelProviderType.OLLAMA, ModelProviderType.JAN}
            else await inquirer.secret(message="Enter API key:", validate=EmptyInputValidator()).execute_async()  # type: ignore
        )

    try:
        if provider_type == ModelProviderType.OLLAMA:
            console.print()
            console.hint(
                "If you are struggling with ollama performance, try increasing the context "
                + "length in ollama UI settings or using an environment variable in the CLI: OLLAMA_CONTEXT_LENGTH=8192"
                + "\nMore information: https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-specify-the-context-window-size\n\n"
            )
            async with httpx.AsyncClient() as client:
                response = (await client.get(f"{base_url}/models", timeout=30.0)).raise_for_status().json()
                available_models = [m.get("id", "") for m in response.get("data", []) or []]
                [recommended_llm_model] = [m for m in RECOMMENDED_LLM_MODELS if m.startswith(ModelProviderType.OLLAMA)]
                [recommended_embedding_model] = [
                    m for m in RECOMMENDED_EMBEDDING_MODELS if m.startswith(ModelProviderType.OLLAMA)
                ]
                recommended_llm_model = recommended_llm_model.removeprefix(f"{ModelProviderType.OLLAMA}:")
                recommended_embedding_model = recommended_embedding_model.removeprefix(f"{ModelProviderType.OLLAMA}:")

                if recommended_llm_model not in available_models:
                    message = f"Do you want to pull the recommended LLM model '{recommended_llm_model}'?"
                    if not available_models:
                        message = f"There are no locally available models in Ollama. {message}"
                    if await inquirer.confirm(message, default=True).execute_async():  # type: ignore
                        await run_command(
                            [_ollama_exe(), "pull", recommended_llm_model], "Pulling the selected model", check=True
                        )

                if recommended_embedding_model not in available_models and (
                    await inquirer.confirm(  # type: ignore
                        message=f"Do you want to pull the recommended embedding model '{recommended_embedding_model}'?",
                        default=True,
                    ).execute_async()
                ):
                    await run_command(
                        [_ollama_exe(), "pull", recommended_embedding_model], "Pulling the selected model", check=True
                    )

        if not use_true_localhost:
            base_url = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", base_url)

        with console.status("Saving configuration...", spinner="dots"):
            return await ModelProvider.create(
                name=provider_name,
                type=ModelProviderType(provider_type),
                base_url=base_url,
                api_key=api_key,
                watsonx_space_id=watsonx_space_id,
                watsonx_project_id=watsonx_project_id,
            )

    except httpx.HTTPError as e:
        if hasattr(e, "response") and hasattr(e.response, "json"):  # pyright: ignore [reportAttributeAccessIssue]
            err = str(e.response.json().get("detail", str(e)))  # pyright: ignore [reportAttributeAccessIssue]
        else:
            err = str(e)
        match provider_type:
            case ModelProviderType.OLLAMA:
                err += "\n\n💡 [bright_cyan]HINT[/bright_cyan]: We could not connect to Ollama. Is it running?"
            case ModelProviderType.JAN:
                err += (
                    "\n\n💡 [bright_cyan]HINT[/bright_cyan]: We could not connect to Jan. Ensure that the server is running: "
                    "in the Jan application, click the [bold][<>][/bold] button and [bold]Start server[/bold]."
                )
            case ModelProviderType.OTHER:
                err += (
                    "\n\n💡 [bright_cyan]HINT[/bright_cyan]: We could not connect to the API URL you have specified."
                    "Is it correct?"
                )
            case _:
                err += f"\n\n💡 [bright_cyan]HINT[/bright_cyan]: {provider_type} may be down or API key is invalid"
        raise ModelProviderError(err) from e


async def _select_default_model(capability: ModelCapability) -> str | None:
    async with openai_client() as client:
        models = (await client.models.list()).data

    recommended_models = RECOMMENDED_LLM_MODELS if capability == ModelCapability.LLM else RECOMMENDED_EMBEDDING_MODELS

    available_models = {m.id for m in models if capability in m.model_dump()["provider"]["capabilities"]}
    if not available_models:
        raise ModelProviderError(
            f"[bold]No models are available[/bold]\n"
            f"Configure at least one working {capability} provider using `beeai model add` command."
        )

    recommended_model = [m for m in recommended_models if m in available_models]
    recommended_model = recommended_model[0] if recommended_model else None

    console.print(f"\n[bold]Configure default model for {capability}[/bold]:")

    selected_model = (
        recommended_model
        if recommended_model
        and await inquirer.confirm(  # type: ignore
            message=f"Do you want to use the recommended model as default: '{recommended_model}'?",
            default=True,
        ).execute_async()
        else (
            await inquirer.fuzzy(  # type: ignore
                message="Select a model to be used as default (type to search):",
                choices=sorted(available_models),
            ).execute_async()
        )
    )
    assert selected_model, "No model selected"

    try:
        with console.status("Checking if the model works...", spinner="dots"):
            async with openai_client() as client:
                if capability == ModelCapability.LLM:
                    test_response = await client.chat.completions.create(
                        model=selected_model,
                        max_completion_tokens=500,  # reasoning models need some tokens to think about this
                        messages=[
                            {
                                "role": "system",
                                "content": "Repeat each message back to the user, verbatim. Don't say anything else.",
                            },
                            {"role": "user", "content": "Hello!"},
                        ],
                    )
                    if not test_response.choices or "Hello" not in (test_response.choices[0].message.content or ""):
                        raise ModelProviderError("Model did not provide a proper response.")
                else:
                    test_response = await client.embeddings.create(model=selected_model, input="Hello!")
                    if not test_response.data or not test_response.data[0].embedding:
                        raise ModelProviderError("Model did not provide a proper response.")
        return selected_model
    except ModelProviderError:
        raise
    except Exception as ex:
        raise ModelProviderError(f"Error during model test: {ex!s}") from ex


@app.command("list")
async def list_models():
    config = await SystemConfiguration.get()
    async with openai_client() as client:
        models = (await client.models.list()).data
        max_id_len = max(len(model.id) for model in models) if models else 0
        max_col_len = max_id_len + len(" (default embedding)")
        with create_table(
            Column("Id", width=max_col_len),
            Column("Owned by"),
            Column("Created", ratio=1),
        ) as model_table:
            for model in sorted(models, key=lambda m: m.id):
                model_id = model.id.ljust(max_id_len)
                if config.default_embedding_model == model.id:
                    model_id += " [blue][bold](default embedding)[/bold][/blue]"
                if config.default_llm_model == model.id:
                    model_id += " [green][bold](default llm)[/bold][/green]"
                model_table.add_row(
                    model_id, model.owned_by, datetime.fromtimestamp(model.created).strftime("%Y-%m-%d")
                )
        console.print(model_table)


async def _reset_configuration(existing_providers: list[ModelProvider] | None = None):
    if not existing_providers:
        existing_providers = await ModelProvider.list()
    for provider in existing_providers:
        await provider.delete()
    await SystemConfiguration.update(default_embedding_model=None, default_llm_model=None)


@app.command("setup")
async def setup(
    use_true_localhost: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    verbose: typing.Annotated[bool, typer.Option("-v")] = False,
):
    """Interactive setup for LLM and embedding provider environment variables"""

    with verbosity(verbose):
        async with configuration.use_platform_client():
            # Delete all existing providers
            existing_providers = await ModelProvider.list()
            if existing_providers:
                console.warning("The following providers are already configured:\n")
                _list_providers(existing_providers)
                console.print()
                if await inquirer.confirm(  # type: ignore
                    message="Do you want to reset the configuration?", default=True
                ).execute_async():
                    with console.status("Resetting configuration...", spinner="dots"):
                        await _reset_configuration(existing_providers)
                else:
                    console.print("[bold]Aborting[/bold] the setup.")
                    sys.exit(1)

            try:
                console.print("[bold]Setting up LLM provider...[/bold]")
                llm_provider = await _add_provider(ModelCapability.LLM, use_true_localhost=use_true_localhost)
                default_llm_model = await _select_default_model(ModelCapability.LLM)

                default_embedding_model = None
                if ModelCapability.EMBEDDING in llm_provider.capabilities:
                    default_embedding_model = await _select_default_model(ModelCapability.EMBEDDING)
                elif await inquirer.confirm(  # type: ignore
                    message="Do you want to configure an embedding provider? (recommended)", default=True
                ).execute_async():
                    console.print("[bold]Setting up embedding provider...[/bold]")
                    await _add_provider(capability=ModelCapability.EMBEDDING, use_true_localhost=use_true_localhost)
                    default_embedding_model = await _select_default_model(ModelCapability.EMBEDDING)

                with console.status("Saving configuration...", spinner="dots"):
                    await SystemConfiguration.update(
                        default_llm_model=default_llm_model,
                        default_embedding_model=default_embedding_model,
                    )
                console.print(
                    "\n[bold green]You're all set![/bold green] "
                    "(You can re-run this setup anytime with [blue]beeai model setup[/blue])"
                )
            except Exception:
                await _reset_configuration()
                raise


@app.command("change | select | default")
async def select_default_model(
    capability: typing.Annotated[
        ModelCapability | None, typer.Argument(help="Which default model to change (llm/embedding)")
    ] = None,
    model_id: typing.Annotated[str | None, typer.Argument(help="Model ID to be used as default")] = None,
):
    if not capability:
        capability = await inquirer.select(  # type: ignore
            message="Which default model would you like to change?",
            choices=[
                Choice(name="llm", value=ModelCapability.LLM),
                Choice(name="embedding", value=ModelCapability.EMBEDDING),
            ],
        ).execute_async()

    assert capability
    async with configuration.use_platform_client():
        model = model_id if model_id else await _select_default_model(capability)
        conf = await SystemConfiguration.get()
        default_llm_model = model if capability == ModelCapability.LLM else conf.default_llm_model
        default_embedding_model = model if capability == ModelCapability.EMBEDDING else conf.default_embedding_model
        with console.status("Saving configuration...", spinner="dots"):
            await SystemConfiguration.update(
                default_llm_model=default_llm_model,
                default_embedding_model=default_embedding_model,
            )


model_provider_app = AsyncTyper()
app.add_typer(model_provider_app, name="provider")


def _list_providers(providers: list[ModelProvider]):
    with create_table(Column("Type"), Column("Name"), Column("Base URL", ratio=1)) as provider_table:
        for provider in providers:
            provider_table.add_row(provider.type, provider.name, str(provider.base_url))
    console.print(provider_table)


@model_provider_app.command("list")
async def list_model_providers():
    async with configuration.use_platform_client():
        providers = await ModelProvider.list()
        _list_providers(providers)


@model_provider_app.command("add")
@app.command("add")
async def add_provider(
    capability: typing.Annotated[
        ModelCapability | None, typer.Argument(help="Which default model to change (llm/embedding)")
    ] = None,
):
    if not capability:
        capability = await inquirer.select(  # type: ignore
            message="Which default provider would you like to add?",
            choices=[
                Choice(name="llm", value=ModelCapability.LLM),
                Choice(name="embedding", value=ModelCapability.EMBEDDING),
            ],
        ).execute_async()

    assert capability
    async with configuration.use_platform_client():
        await _add_provider(capability)

        conf = await SystemConfiguration.get()
        default_model = conf.default_llm_model if capability == ModelCapability.LLM else conf.default_embedding_model
        if not default_model:
            default_model = await _select_default_model(capability)
            default_llm = default_model if capability == ModelCapability.LLM else conf.default_llm_model
            default_embedding = (
                default_model if capability == ModelCapability.EMBEDDING else conf.default_embedding_model
            )
            with console.status("Saving configuration...", spinner="dots"):
                await SystemConfiguration.update(
                    default_llm_model=default_llm, default_embedding_model=default_embedding
                )


def _select_provider(providers: list[ModelProvider], search_path: str) -> ModelProvider:
    search_path = search_path.lower()
    provider_candidates = {p.id: p for p in providers if search_path in p.type.lower()}
    provider_candidates.update({p.id: p for p in providers if search_path in str(p.base_url).lower()})
    if len(provider_candidates) != 1:
        provider_candidates = [f"  - {c}" for c in provider_candidates]
        remove_providers_detail = ":\n" + "\n".join(provider_candidates) if provider_candidates else ""
        raise ValueError(f"{len(provider_candidates)} matching providers{remove_providers_detail}")
    [selected_provider] = provider_candidates.values()
    return selected_provider


@model_provider_app.command("remove | rm | delete")
@app.command("remove | rm | delete")
async def remove_provider(
    search_path: typing.Annotated[
        str | None, typer.Argument(..., help="Provider type or part of the provider base url")
    ] = None,
):
    async with configuration.use_platform_client():
        conf = await SystemConfiguration.get()

        async with configuration.use_platform_client():
            providers = await ModelProvider.list()

        if not search_path:
            provider: ModelProvider = await inquirer.select(  # type: ignore
                message="Choose a provider to remove:",
                choices=[Choice(name=f"{p.type} ({p.base_url})", value=p) for p in providers],
            ).execute_async()
        else:
            provider = _select_provider(providers, search_path)

        await provider.delete()

        default_llm = None if (conf.default_llm_model or "").startswith(provider.type) else conf.default_llm_model
        default_embed = (
            None if (conf.default_embedding_model or "").startswith(provider.type) else conf.default_embedding_model
        )

        try:
            if (conf.default_llm_model or "").startswith(provider.type):
                console.print("The provider was used as default llm model. Please select another one...")
                default_llm = await _select_default_model(ModelCapability.LLM)
            if (conf.default_embedding_model or "").startswith(provider.type):
                console.print("The provider was used as default embedding model. Please select another one...")
                default_embed = await _select_default_model(ModelCapability.EMBEDDING)
        finally:
            await SystemConfiguration.update(default_llm_model=default_llm, default_embedding_model=default_embed)

    await list_model_providers()


async def ensure_llm_provider():
    async with configuration.use_platform_client():
        config = await SystemConfiguration.get()
        async with openai_client() as client:
            models = (await client.models.list()).data
            models = {m.id for m in models}

        inconsistent = False
        if (config.default_embedding_model and config.default_embedding_model not in models) or (
            config.default_llm_model and config.default_llm_model not in models
        ):
            console.warning("Found inconsistent configuration: default model is not found in available models.")
            inconsistent = True

        if config.default_llm_model and not inconsistent:
            return

    console.print("[bold]Welcome to 🐝 [red]BeeAI[/red]![/bold]")
    console.print("Let's start by configuring your LLM environment.\n")
    try:
        await setup()
    except Exception:
        console.error("Could not continue because the LLM environment is not properly set up.")
        console.hint("Try re-entering your LLM API details with: [green]beeai model setup[/green]")
        raise
    console.print()
