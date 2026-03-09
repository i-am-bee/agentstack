# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import functools
import os
import re
import shutil
import sys
import typing
from datetime import datetime

import httpx
import typer
from agentstack_sdk.platform import (
    ModelCapability,
    ModelProvider,
    ModelProviderType,
    SystemConfiguration,
)
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.table import Column

from agentstack_cli.api import openai_client
from agentstack_cli.async_typer import AsyncTyper, console, create_table
from agentstack_cli.configuration import Configuration
from agentstack_cli.server_utils import announce_server_action, confirm_server_action
from agentstack_cli.utils import run_command, verbosity

app = AsyncTyper()
configuration = Configuration()


class ModelProviderError(Exception): ...


@functools.cache
def _ollama_exe() -> str:
    for exe in ("ollama", "ollama.exe", os.environ.get("LOCALAPPDATA", "") + "\\Programs\\Ollama\\ollama.exe"):
        if shutil.which(exe):
            return exe
    raise RuntimeError("Ollama executable not found")


RECOMMENDED_LLM_MODELS = [
    f"{ModelProviderType.WATSONX}:ibm/granite-3-3-8b-instruct",
    f"{ModelProviderType.BEDROCK}:deepseek.v3.2",
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
        name="Amazon Bedrock".ljust(20) + "🧪 experimental",
        value=(ModelProviderType.BEDROCK, "Amazon Bedrock", None),
    ),
    Choice(
        name="Anthropic Claude".ljust(20),
        value=(ModelProviderType.ANTHROPIC, "Anthropic Claude", "https://api.anthropic.com/v1"),
    ),
    Choice(
        name="Cerebras".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.CEREBRAS, "Cerebras", "https://api.cerebras.ai/v1"),
    ),
    Choice(
        name="Chutes".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.CHUTES, "Chutes", "https://llm.chutes.ai/v1"),
    ),
    Choice(
        name="Cohere".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.COHERE, "Cohere", "https://api.cohere.ai/compatibility/v1"),
    ),
    Choice(name="DeepSeek", value=(ModelProviderType.DEEPSEEK, "DeepSeek", "https://api.deepseek.com/v1")),
    Choice(
        name="Google Gemini".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.GEMINI, "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
    ),
    Choice(
        name="GitHub Models".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.GITHUB, "GitHub Models", "https://models.github.ai/inference"),
    ),
    Choice(
        name="Groq".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.GROQ, "Groq", "https://api.groq.com/openai/v1"),
    ),
    Choice(name="IBM watsonx".ljust(20), value=(ModelProviderType.WATSONX, "IBM watsonx", None)),
    Choice(name="Jan".ljust(20) + "💻 local", value=(ModelProviderType.JAN, "Jan", "http://localhost:1337/v1")),
    Choice(
        name="Mistral".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.MISTRAL, "Mistral", "https://api.mistral.ai/v1"),
    ),
    Choice(
        name="Moonshot AI".ljust(20),
        value=(ModelProviderType.MOONSHOT, "Moonshot AI", "https://api.moonshot.ai/v1"),
    ),
    Choice(
        name="NVIDIA NIM".ljust(20),
        value=(ModelProviderType.NVIDIA, "NVIDIA NIM", "https://integrate.api.nvidia.com/v1"),
    ),
    Choice(
        name="Ollama".ljust(20) + "💻 local",
        value=(ModelProviderType.OLLAMA, "Ollama", "http://localhost:11434/v1"),
    ),
    Choice(
        name="OpenAI".ljust(20),
        value=(ModelProviderType.OPENAI, "OpenAI", "https://api.openai.com/v1"),
    ),
    Choice(
        name="OpenRouter".ljust(20) + "🆓 has some free models",
        value=(ModelProviderType.OPENROUTER, "OpenRouter", "https://openrouter.ai/api/v1"),
    ),
    Choice(
        name="Perplexity".ljust(20),
        value=(ModelProviderType.PERPLEXITY, "Perplexity", "https://api.perplexity.ai"),
    ),
    Choice(
        name="Together.ai".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.TOGETHER, "together.ai", "https://api.together.xyz/v1"),
    ),
    Choice(
        name="🛠️  Other (RITS, vLLM, ..., any OpenAI-compatible API)",
        value=(ModelProviderType.OTHER, "Other", None),
    ),
]

EMBEDDING_PROVIDERS = [
    Choice(
        name="Cohere".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.COHERE, "Cohere", "https://api.cohere.ai/compatibility/v1"),
    ),
    Choice(
        name="Google Gemini".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.GEMINI, "Gemini", "https://generativelanguage.googleapis.com/v1beta/openai"),
    ),
    Choice(
        name="IBM watsonx".ljust(20),
        value=(ModelProviderType.WATSONX, "IBM watsonx", None),
    ),
    Choice(
        name="Mistral".ljust(20) + "🆓 has a free tier",
        value=(ModelProviderType.MISTRAL, "Mistral", "https://api.mistral.ai/v1"),
    ),
    Choice(
        name="Ollama".ljust(20) + "💻 local",
        value=(ModelProviderType.OLLAMA, "Ollama", "http://localhost:11434/v1"),
    ),
    Choice(
        name="OpenAI".ljust(20),
        value=(ModelProviderType.OPENAI, "OpenAI", "https://api.openai.com/v1"),
    ),
    Choice(
        name="Voyage".ljust(20),
        value=(ModelProviderType.VOYAGE, "Voyage", "https://api.voyageai.com/v1"),
    ),
    Choice(
        name="🛠️  Other (vLLM, ..., any OpenAI-compatible API)",
        value=(ModelProviderType.OTHER, "Other", None),
    ),
]


async def _add_provider(
    capability: ModelCapability,
    use_true_localhost: bool = False,
    *,
    provider_type_str: str | None = None,
    api_key: str | None = None,
    base_url_override: str | None = None,
    watsonx_region: str | None = None,
    watsonx_project_or_space: str | None = None,
    watsonx_project_or_space_id: str | None = None,
    bedrock_region: str | None = None,
    bedrock_access_key: str | None = None,
    bedrock_secret_key: str | None = None,
    auto_pull_models: bool | None = None,
) -> ModelProvider:
    provider_type: str
    provider_name: str
    base_url: str
    _watsonx_project_id, _watsonx_space_id = None, None
    choices = LLM_PROVIDERS if capability == ModelCapability.LLM else EMBEDDING_PROVIDERS

    if provider_type_str is not None:
        matched = [c.value for c in choices if c.value[0].lower() == provider_type_str.lower()]
        if not matched:
            raise ValueError(
                f"Unknown provider type: '{provider_type_str}'. "
                f"Available: {[c.value[0] for c in choices]}"
            )
        provider_type, provider_name, base_url = matched[0]
    else:
        provider_type, provider_name, base_url = await inquirer.fuzzy(
            message=f"Select {capability} provider (type to search):", choices=choices
        ).execute_async() or sys.exit(1)

    _watsonx_project_or_space: str = ""
    _watsonx_project_or_space_id: str = ""

    if provider_type == ModelProviderType.OTHER:
        if base_url_override is not None:
            base_url = base_url_override.rstrip("/")
        else:
            base_url = await inquirer.text(
                message="Enter the base URL of your API (OpenAI-compatible):",
                validate=lambda url: url.startswith(("http://", "https://")),
                transformer=lambda url: url.rstrip("/"),
            ).execute_async() or sys.exit(1)
        if re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm\.com/.*$", base_url):
            provider_type = ModelProviderType.RITS
            if not base_url.endswith("/v1"):
                base_url = base_url.removesuffix("/") + "/v1"

    if provider_type == ModelProviderType.WATSONX:
        if watsonx_region is not None:
            region = watsonx_region
        else:
            region = await inquirer.select(
                message="Select IBM Cloud region:",
                choices=[
                    Choice(name="us-south", value="us-south"),
                    Choice(name="ca-tor", value="ca-tor"),
                    Choice(name="eu-gb", value="eu-gb"),
                    Choice(name="eu-de", value="eu-de"),
                    Choice(name="jp-tok", value="jp-tok"),
                    Choice(name="au-syd", value="au-syd"),
                ],
            ).execute_async() or sys.exit(1)
        base_url = f"https://{region}.ml.cloud.ibm.com"

        if watsonx_project_or_space is not None:
            _watsonx_project_or_space = watsonx_project_or_space
        else:
            _watsonx_project_or_space = await inquirer.select(
                "Use a Project or a Space?", choices=["project", "space"]
            ).execute_async() or sys.exit(1)

        if watsonx_project_or_space_id is not None:
            _watsonx_project_or_space_id = watsonx_project_or_space_id
        elif (
            not (env_id := os.environ.get(f"WATSONX_{_watsonx_project_or_space.upper()}_ID", ""))
            or not await inquirer.confirm(
                message=f"Use the {_watsonx_project_or_space} id from environment variable 'WATSONX_{_watsonx_project_or_space.upper()}_ID'?",
                default=True,
            ).execute_async()
        ):
            _watsonx_project_or_space_id = await inquirer.text(
                message=f"Enter the {_watsonx_project_or_space} id:"
            ).execute_async() or sys.exit(1)
        else:
            _watsonx_project_or_space_id = env_id

        _watsonx_project_id = _watsonx_project_or_space_id if _watsonx_project_or_space == "project" else None
        _watsonx_space_id = _watsonx_project_or_space_id if _watsonx_project_or_space == "space" else None

    _api_key: str
    if provider_type == ModelProviderType.BEDROCK:
        if bedrock_region is not None:
            region = bedrock_region
        else:
            region: str = await inquirer.select(
                message="Select AWS Region:",
                choices=[
                    Choice(name="us-east-1", value="us-east-1"),
                    Choice(name="us-west-2", value="us-west-2"),
                    Choice(name="eu-central-1", value="eu-central-1"),
                    Choice(name="ap-northeast-1", value="ap-northeast-1"),
                    Choice(name="ap-southeast-1", value="ap-southeast-1"),
                ],
            ).execute_async() or sys.exit(1)

        base_url = f"https://bedrock-runtime.{region}.amazonaws.com/openai/v1"

        if api_key is not None:
            _api_key = api_key
        elif bedrock_access_key is not None and bedrock_secret_key is not None:
            _api_key = f"{bedrock_access_key}:{bedrock_secret_key}::{region}"
        else:
            access_key = await inquirer.secret(message="AWS Access Key ID:").execute_async() or ""
            secret_key = await inquirer.secret(message="AWS Secret Access Key:").execute_async() or ""
            _api_key = f"{access_key}:{secret_key}::{region}"
    elif provider_type in {ModelProviderType.OLLAMA, ModelProviderType.JAN}:
        _api_key = "dummy"
    elif api_key is not None:
        _api_key = api_key
    elif (env_api_key := os.environ.get(f"{provider_type.upper()}_API_KEY")) and await inquirer.confirm(
        message=f"Use the API key from environment variable '{provider_type.upper()}_API_KEY'?",
        default=True,
    ).execute_async():
        _api_key = env_api_key
    else:
        _api_key = await inquirer.secret(message="Enter API key:").execute_async() or ""

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
                    pull_msg = f"Do you want to pull the recommended LLM model '{recommended_llm_model}'?"
                    if not available_models:
                        pull_msg = f"There are no locally available models in Ollama. {pull_msg}"
                    pull = (
                        auto_pull_models
                        if auto_pull_models is not None
                        else await inquirer.confirm(pull_msg, default=True).execute_async()
                    )
                    if pull:
                        await run_command(
                            [_ollama_exe(), "pull", recommended_llm_model], "Pulling the selected model", check=True
                        )

                if recommended_embedding_model not in available_models:
                    pull = (
                        auto_pull_models
                        if auto_pull_models is not None
                        else await inquirer.confirm(
                            message=f"Do you want to pull the recommended embedding model '{recommended_embedding_model}'?",
                            default=True,
                        ).execute_async()
                    )
                    if pull:
                        await run_command(
                            [_ollama_exe(), "pull", recommended_embedding_model], "Pulling the selected model", check=True
                        )

        if not use_true_localhost:
            base_url = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", base_url)

        with console.status("Saving configuration...", spinner="dots"):
            provider = await ModelProvider.create(
                name=provider_name,
                type=ModelProviderType(provider_type),
                base_url=base_url,
                api_key=_api_key,
                watsonx_space_id=_watsonx_space_id,
                watsonx_project_id=_watsonx_project_id,
            )
            return provider

    except httpx.HTTPError as e:
        if hasattr(e, "response") and hasattr(e.response, "json"):
            err = str(e.response.json().get("detail", str(e)))
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


async def _select_default_model(
    capability: ModelCapability,
    *,
    model_id: str | None = None,
    yes: bool = False,
) -> str | None:
    async with openai_client() as client:
        models = (await client.models.list()).data

    recommended_models = RECOMMENDED_LLM_MODELS if capability == ModelCapability.LLM else RECOMMENDED_EMBEDDING_MODELS

    available_models = {m.id for m in models if capability in m.model_dump()["provider"]["capabilities"]}
    if not available_models:
        raise ModelProviderError(
            f"[bold]No models are available[/bold]\n"
            f"Configure at least one working {capability} provider using `agentstack model add` command."
        )

    recommended_model = [m for m in recommended_models if m in available_models]
    recommended_model = recommended_model[0] if recommended_model else None

    console.print(f"\n[bold]Configure default model for {capability}[/bold]:")

    if model_id is not None:
        if model_id not in available_models:
            raise ModelProviderError(
                f"Model '{model_id}' is not available. Available models: {sorted(available_models)}"
            )
        selected_model = model_id
    elif yes and recommended_model:
        selected_model = recommended_model
    elif yes:
        selected_model = sorted(available_models)[0]
    else:
        selected_model = (
            recommended_model
            if recommended_model
            and await inquirer.confirm(
                message=f"Do you want to use the recommended model as default: '{recommended_model}'?",
                default=True,
            ).execute_async()
            else (
                await inquirer.fuzzy(
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
                        # reasoning models need some tokens to think about this
                        max_completion_tokens=500 if not selected_model.startswith("mistral") else None,
                        messages=[
                            {
                                "role": "system",
                                "content": "Repeat each message back to the user, verbatim. Don't say anything else.",
                            },
                            {"role": "user", "content": "Hello!"},
                        ],
                    )
                    console.print(f"DEBUG response: choices={test_response.choices!r}")
                    if test_response.choices:
                        console.print(f"DEBUG content: {test_response.choices[0].message.content!r}")
                    if not test_response.choices or "hello" not in (test_response.choices[0].message.content or "").lower():
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
    """List all available models."""
    announce_server_action("Listing models on")
    async with configuration.use_platform_client():
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


@app.command("setup", help="Interactive setup for LLM and embedding provider environment variables [Admin only]")
async def setup(
    use_true_localhost: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    verbose: typing.Annotated[bool, typer.Option("-v", "--verbose", help="Show verbose output")] = False,
    llm_provider: typing.Annotated[
        str | None, typer.Option("--llm-provider", help="LLM provider type (e.g. openai, anthropic, watsonx)")
    ] = None,
    llm_api_key: typing.Annotated[
        str | None, typer.Option("--llm-api-key", help="LLM provider API key")
    ] = None,
    llm_base_url: typing.Annotated[
        str | None, typer.Option("--llm-base-url", help="Base URL for 'other' LLM provider")
    ] = None,
    llm_watsonx_region: typing.Annotated[
        str | None, typer.Option("--llm-watsonx-region", help="IBM watsonx region for LLM (e.g. us-south)")
    ] = None,
    llm_watsonx_project_or_space: typing.Annotated[
        str | None, typer.Option("--llm-watsonx-project-or-space", help="IBM watsonx: 'project' or 'space'")
    ] = None,
    llm_watsonx_project_or_space_id: typing.Annotated[
        str | None, typer.Option("--llm-watsonx-project-or-space-id", help="IBM watsonx project or space ID for LLM")
    ] = None,
    llm_model: typing.Annotated[
        str | None, typer.Option("--llm-model", help="Default LLM model ID (e.g. openai:gpt-4o)")
    ] = None,
    llm_bedrock_region: typing.Annotated[
        str | None, typer.Option("--llm-bedrock-region", help="AWS region for Bedrock LLM (e.g. us-east-1)")
    ] = None,
    llm_bedrock_access_key: typing.Annotated[
        str | None, typer.Option("--llm-bedrock-access-key", help="AWS Access Key ID for Bedrock LLM")
    ] = None,
    llm_bedrock_secret_key: typing.Annotated[
        str | None, typer.Option("--llm-bedrock-secret-key", help="AWS Secret Access Key for Bedrock LLM")
    ] = None,
    embedding_provider: typing.Annotated[
        str | None, typer.Option("--embedding-provider", help="Embedding provider type (e.g. openai, watsonx)")
    ] = None,
    embedding_api_key: typing.Annotated[
        str | None, typer.Option("--embedding-api-key", help="Embedding provider API key")
    ] = None,
    embedding_base_url: typing.Annotated[
        str | None, typer.Option("--embedding-base-url", help="Base URL for 'other' embedding provider")
    ] = None,
    embedding_watsonx_region: typing.Annotated[
        str | None, typer.Option("--embedding-watsonx-region", help="IBM watsonx region for embedding")
    ] = None,
    embedding_watsonx_project_or_space: typing.Annotated[
        str | None, typer.Option("--embedding-watsonx-project-or-space", help="IBM watsonx: 'project' or 'space'")
    ] = None,
    embedding_watsonx_project_or_space_id: typing.Annotated[
        str | None,
        typer.Option("--embedding-watsonx-project-or-space-id", help="IBM watsonx project or space ID for embedding"),
    ] = None,
    embedding_model: typing.Annotated[
        str | None, typer.Option("--embedding-model", help="Default embedding model ID")
    ] = None,
    embedding_bedrock_region: typing.Annotated[
        str | None, typer.Option("--embedding-bedrock-region", help="AWS region for Bedrock embedding (e.g. us-east-1)")
    ] = None,
    embedding_bedrock_access_key: typing.Annotated[
        str | None, typer.Option("--embedding-bedrock-access-key", help="AWS Access Key ID for Bedrock embedding")
    ] = None,
    embedding_bedrock_secret_key: typing.Annotated[
        str | None, typer.Option("--embedding-bedrock-secret-key", help="AWS Secret Access Key for Bedrock embedding")
    ] = None,
    skip_embedding: typing.Annotated[
        bool, typer.Option("--skip-embedding", help="Skip embedding provider setup")
    ] = False,
    yes: typing.Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompts and auto-select recommended models"),
    ] = False,
):
    """Interactive setup for LLM and embedding provider environment variables"""
    announce_server_action("Configuring model providers for")

    with verbosity(verbose):
        async with configuration.use_platform_client():
            # Delete all existing providers
            existing_providers = await ModelProvider.list()
            if existing_providers:
                console.warning("The following providers are already configured:\n")
                _list_providers(existing_providers)
                console.print()
                if yes or await inquirer.confirm(
                    message="Do you want to reset the configuration?", default=True
                ).execute_async():
                    with console.status("Resetting configuration...", spinner="dots"):
                        await _reset_configuration(existing_providers)
                else:
                    console.print("[bold]Aborting[/bold] the setup.")
                    sys.exit(1)

            try:
                console.print("[bold]Setting up LLM provider...[/bold]")
                llm_provider_obj = await _add_provider(
                    ModelCapability.LLM,
                    use_true_localhost=use_true_localhost,
                    provider_type_str=llm_provider,
                    api_key=llm_api_key,
                    base_url_override=llm_base_url,
                    watsonx_region=llm_watsonx_region,
                    watsonx_project_or_space=llm_watsonx_project_or_space,
                    watsonx_project_or_space_id=llm_watsonx_project_or_space_id,
                    bedrock_region=llm_bedrock_region,
                    bedrock_access_key=llm_bedrock_access_key,
                    bedrock_secret_key=llm_bedrock_secret_key,
                    auto_pull_models=yes,
                )
                default_llm_model = await _select_default_model(ModelCapability.LLM, model_id=llm_model, yes=yes)

                default_embedding_model = None
                if skip_embedding:
                    console.hint(
                        "Skipping embedding setup. You can add an embedding provider later with: [green]agentstack model add[/green]"
                    )
                elif embedding_provider is not None:
                    console.print("[bold]Setting up embedding provider...[/bold]")
                    await _add_provider(
                        capability=ModelCapability.EMBEDDING,
                        use_true_localhost=use_true_localhost,
                        provider_type_str=embedding_provider,
                        api_key=embedding_api_key,
                        base_url_override=embedding_base_url,
                        watsonx_region=embedding_watsonx_region,
                        watsonx_project_or_space=embedding_watsonx_project_or_space,
                        watsonx_project_or_space_id=embedding_watsonx_project_or_space_id,
                        bedrock_region=embedding_bedrock_region,
                        bedrock_access_key=embedding_bedrock_access_key,
                        bedrock_secret_key=embedding_bedrock_secret_key,
                    )
                    default_embedding_model = await _select_default_model(
                        ModelCapability.EMBEDDING, model_id=embedding_model, yes=yes
                    )
                elif (
                    ModelCapability.EMBEDDING in llm_provider_obj.capabilities
                    and llm_provider_obj.type
                    != ModelProviderType.RITS  # RITS does not support embeddings, but we treat it as OTHER
                    and (
                        llm_provider_obj.type != ModelProviderType.OTHER  # OTHER may not support embeddings, so we ask
                        or yes
                        or inquirer.confirm(
                            "Do you want to also set up an embedding model from the same provider?", default=True
                        )
                    )
                ):
                    default_embedding_model = await _select_default_model(
                        ModelCapability.EMBEDDING, model_id=embedding_model, yes=yes
                    )
                elif yes or await inquirer.confirm(
                    message="Do you want to configure an embedding provider? (recommended)", default=True
                ).execute_async():
                    console.print("[bold]Setting up embedding provider...[/bold]")
                    await _add_provider(capability=ModelCapability.EMBEDDING, use_true_localhost=use_true_localhost)
                    default_embedding_model = await _select_default_model(ModelCapability.EMBEDDING, yes=yes)
                else:
                    console.hint("You can add an embedding provider later with: [green]agentstack model add[/green]")

                with console.status("Saving configuration...", spinner="dots"):
                    await SystemConfiguration.update(
                        default_llm_model=default_llm_model,
                        default_embedding_model=default_embedding_model,
                    )
                console.print(
                    "\n[bold green]You're all set![/bold green] "
                    "(You can re-run this setup anytime with [blue]agentstack model setup[/blue])"
                )
            except Exception:
                await _reset_configuration()
                raise


@app.command("change | select | default", help="Change the default model [Admin only]")
async def select_default_model(
    capability: typing.Annotated[
        ModelCapability | None, typer.Argument(help="Which default model to change (llm/embedding)")
    ] = None,
    model_id: typing.Annotated[str | None, typer.Argument(help="Model ID to be used as default")] = None,
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
):
    url = announce_server_action("Updating default model for")
    await confirm_server_action("Proceed with updating default model on", url=url, yes=yes)
    if not capability:
        capability = await inquirer.select(
            message="Which default model would you like to change?",
            choices=[
                Choice(name="llm", value=ModelCapability.LLM),
                Choice(name="embedding", value=ModelCapability.EMBEDDING),
            ],
        ).execute_async()

    assert capability
    capability_name = str(getattr(capability, "value", capability)).lower()
    await confirm_server_action(f"Proceed with updating the default {capability_name} model on", url=url, yes=yes)
    async with configuration.use_platform_client():
        model = model_id if model_id else await _select_default_model(capability, yes=yes)
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
    with create_table(Column("Type"), Column("Name"), Column("State"), Column("Base URL", ratio=1)) as provider_table:
        for provider in providers:
            provider_table.add_row(
                provider.type,
                provider.name,
                {
                    "online": "[green]● connected[/green]",
                    "offline": "[bright_black]○ disconnected[/bright_black]",
                }.get(provider.state, provider.state or "<unknown>"),
                str(provider.base_url),
            )
    console.print(provider_table)


@model_provider_app.command("list")
async def list_model_providers():
    """List all available model providers."""
    announce_server_action("Listing model providers on")
    async with configuration.use_platform_client():
        providers = await ModelProvider.list()
        _list_providers(providers)


@model_provider_app.command("add", help="Add a new model provider [Admin only]")
@app.command("add")
async def add_provider(
    capability: typing.Annotated[
        ModelCapability | None, typer.Argument(help="Which default model to change (llm/embedding)")
    ] = None,
    provider: typing.Annotated[
        str | None, typer.Option("--provider", help="Provider type (e.g. openai, anthropic, watsonx)")
    ] = None,
    api_key: typing.Annotated[
        str | None, typer.Option("--api-key", help="Provider API key")
    ] = None,
    base_url: typing.Annotated[
        str | None, typer.Option("--base-url", help="Base URL for 'other' provider")
    ] = None,
    watsonx_region: typing.Annotated[
        str | None, typer.Option("--watsonx-region", help="IBM watsonx region")
    ] = None,
    watsonx_project_or_space: typing.Annotated[
        str | None, typer.Option("--watsonx-project-or-space", help="IBM watsonx: 'project' or 'space'")
    ] = None,
    watsonx_project_or_space_id: typing.Annotated[
        str | None, typer.Option("--watsonx-project-or-space-id", help="IBM watsonx project or space ID")
    ] = None,
    bedrock_region: typing.Annotated[
        str | None, typer.Option("--bedrock-region", help="AWS region for Bedrock (e.g. us-east-1)")
    ] = None,
    bedrock_access_key: typing.Annotated[
        str | None, typer.Option("--bedrock-access-key", help="AWS Access Key ID for Bedrock")
    ] = None,
    bedrock_secret_key: typing.Annotated[
        str | None, typer.Option("--bedrock-secret-key", help="AWS Secret Access Key for Bedrock")
    ] = None,
    model: typing.Annotated[
        str | None, typer.Option("--model", help="Default model ID to use after adding the provider")
    ] = None,
    yes: typing.Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompts and auto-select recommended model")
    ] = False,
):
    """Add a new model provider. [Admin only]"""
    announce_server_action("Adding provider for")
    if not capability:
        capability = await inquirer.select(
            message="Which default provider would you like to add?",
            choices=[
                Choice(name="llm", value=ModelCapability.LLM),
                Choice(name="embedding", value=ModelCapability.EMBEDDING),
            ],
        ).execute_async()

    assert capability
    async with configuration.use_platform_client():
        await _add_provider(
            capability,
            provider_type_str=provider,
            api_key=api_key,
            base_url_override=base_url,
            watsonx_region=watsonx_region,
            watsonx_project_or_space=watsonx_project_or_space,
            watsonx_project_or_space_id=watsonx_project_or_space_id,
            bedrock_region=bedrock_region,
            bedrock_access_key=bedrock_access_key,
            bedrock_secret_key=bedrock_secret_key,
            auto_pull_models=yes,
        )

        conf = await SystemConfiguration.get()
        default_model = conf.default_llm_model if capability == ModelCapability.LLM else conf.default_embedding_model
        if not default_model:
            default_model = await _select_default_model(capability, model_id=model, yes=yes)
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


@model_provider_app.command("remove | rm | delete", help="Remove a model provider [Admin only]")
@app.command("remove | rm | delete")
async def remove_provider(
    search_path: typing.Annotated[
        str | None, typer.Argument(..., help="Provider type or part of the provider base url")
    ] = None,
    yes: typing.Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompts.")] = False,
):
    descriptor = search_path or "selected provider"
    url = announce_server_action(f"Removing model provider '{descriptor}' from")
    await confirm_server_action("Proceed with removing the selected model provider from", url=url, yes=yes)
    async with configuration.use_platform_client():
        conf = await SystemConfiguration.get()

        async with configuration.use_platform_client():
            providers = await ModelProvider.list()

        provider: ModelProvider = (
            _select_provider(providers, search_path)
            if search_path
            else await inquirer.select(
                message="Choose a provider to remove:",
                choices=[Choice(name=f"{p.type} ({p.base_url})", value=p) for p in providers],
            ).execute_async()
            or sys.exit(1)
        )

        await provider.delete()

        default_llm = None if (conf.default_llm_model or "").startswith(provider.type) else conf.default_llm_model
        default_embed = (
            None if (conf.default_embedding_model or "").startswith(provider.type) else conf.default_embedding_model
        )

        try:
            if (conf.default_llm_model or "").startswith(provider.type):
                console.print("The provider was used as default llm model. Please select another one...")
                default_llm = await _select_default_model(ModelCapability.LLM, yes=yes)
            if (conf.default_embedding_model or "").startswith(provider.type):
                console.print("The provider was used as default embedding model. Please select another one...")
                default_embed = await _select_default_model(ModelCapability.EMBEDDING, yes=yes)
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

    console.print("[bold]Welcome to [red]Agent Stack[/red]![/bold]")
    console.print("Let's start by configuring your LLM environment.\n")
    try:
        await setup()
    except Exception:
        console.error("Could not continue because the LLM environment is not properly set up.")
        console.hint("Try re-entering your LLM API details with: [green]agentstack model setup[/green]")
        raise
    console.print()
