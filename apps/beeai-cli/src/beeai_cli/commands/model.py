# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


import functools
import os
import re
import shutil
import sys
import tempfile
import typing

import anyio
import httpx
import typer
from beeai_sdk.platform import ModelProvider, ModelProviderType, SystemConfiguration
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator

from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.configuration import Configuration
from beeai_cli.utils import format_error, run_command, verbosity

app = AsyncTyper()
configuration = Configuration()


@functools.cache
def _ollama_exe() -> str:
    for exe in ("ollama", "ollama.exe"):
        if shutil.which(exe):
            return exe
    raise RuntimeError("Ollama executable not found")


LLM_PROVIDERS = [
    Choice(
        name="Anthropic Claude".ljust(25),
        value=(
            ModelProviderType.ANTHROPIC,
            "Anthropic Claude",
            "https://api.anthropic.com/v1",
            "claude-sonnet-4-20250514",
        ),
    ),
    Choice(
        name="Cerebras".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.CEREBRAS, "Cerebras", "https://api.cerebras.ai/v1", "llama-3.3-70b"),
    ),
    Choice(
        name="Chutes".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.CHUTES, "Chutes", "https://llm.chutes.ai/v1", None),
    ),
    Choice(
        name="Cohere".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.COHERE, "Cohere", "https://api.cohere.ai/compatibility/v1", "command-r-plus"),
    ),
    Choice(
        name="DeepSeek",
        value=(ModelProviderType.DEEPSEEK, "DeepSeek", "https://api.deepseek.com/v1", "deepseek-reasoner"),
    ),
    Choice(
        name="Google Gemini".ljust(25) + "🆓 has a free tier",
        value=(
            ModelProviderType.GEMINI,
            "Google Gemini",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            "models/gemini-2.5-pro",
        ),
    ),
    Choice(
        name="GitHub Models".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.GITHUB, "GitHub Models", "https://models.github.ai/inference", "openai/gpt-4o"),
    ),
    Choice(
        name="Groq".ljust(25) + "🆓 has a free tier",
        value=(
            ModelProviderType.GROQ,
            "Groq",
            "https://api.groq.com/openai/v1",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ),
    ),
    Choice(
        name="IBM watsonx".ljust(25),
        value=(ModelProviderType.WATSONX, "IBM watsonx", None, "ibm/granite-3-3-8b-instruct"),
    ),
    Choice(name="Jan".ljust(25) + "💻 local", value=(ModelProviderType.JAN, "Jan", "http://localhost:1337/v1", None)),
    Choice(
        name="Mistral".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.MISTRAL, "Mistral", "https://api.mistral.ai/v1", "mistral-large-latest"),
    ),
    Choice(
        name="Moonshot AI".ljust(25),
        value=(ModelProviderType.MOONSHOT, "Moonshot AI", "https://api.moonshot.ai/v1", "kimi-latest"),
    ),
    Choice(
        name="NVIDIA NIM".ljust(25),
        value=(
            ModelProviderType.NVIDIA,
            "NVIDIA NIM",
            "https://integrate.api.nvidia.com/v1",
            "deepseek-ai/deepseek-r1",
        ),
    ),
    Choice(
        name=ModelProviderType.OLLAMA.ljust(25) + "💻 local",
        value=(ModelProviderType.OLLAMA, ModelProviderType.OLLAMA, "http://localhost:11434/v1", "granite3.3:8b"),
    ),
    Choice(
        name="OpenAI".ljust(25),
        value=(ModelProviderType.OPENAI, "OpenAI", "https://api.openai.com/v1", "gpt-4o"),
    ),
    Choice(
        name="OpenRouter".ljust(25) + "🆓 has some free models",
        value=(
            ModelProviderType.OPENROUTER,
            "OpenRouter",
            "https://openrouter.ai/api/v1",
            "deepseek/deepseek-r1-distill-llama-70b:free",
        ),
    ),
    Choice(
        name="Perplexity".ljust(25),
        value=(ModelProviderType.PERPLEXITY, "Perplexity", "https://api.perplexity.ai", None),
    ),
    Choice(
        name="together.ai".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.TOGETHER, "together.ai", "https://api.together.xyz/v1", "deepseek-ai/DeepSeek-R1"),
    ),
    Choice(
        name="Other (RITS, vLLM, ...)".ljust(25) + "🔧 provide API URL",
        value=(ModelProviderType.OTHER, "Other", None, None),
    ),
]

EMBEDDING_PROVIDERS = [
    Choice(
        name="Cohere".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.COHERE, "Cohere", "https://api.cohere.ai/compatibility/v1", "embed-multilingual-v3.0"),
    ),
    Choice(
        name="Google Gemini".ljust(25) + "🆓 has a free tier",
        value=(
            ModelProviderType.GEMINI,
            "Gemini",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            "models/gemini-embedding-001",
        ),
    ),
    Choice(
        name="IBM watsonx".ljust(25),
        value=(ModelProviderType.WATSONX, "IBM watsonx", None, "ibm/granite-embedding-278m-multilingual"),
    ),
    Choice(
        name="Mistral".ljust(25) + "🆓 has a free tier",
        value=(ModelProviderType.MISTRAL, "Mistral", "https://api.mistral.ai/v1", "mistral-embed"),
    ),
    Choice(
        name=ModelProviderType.OLLAMA.ljust(25) + "💻 local",
        value=(ModelProviderType.OLLAMA, "Ollama", "http://localhost:11434/v1", "nomic-embed-text:latest"),
    ),
    Choice(
        name="OpenAI".ljust(25),
        value=(ModelProviderType.OPENAI, "OpenAI", "https://api.openai.com/v1", "text-embedding-3-small"),
    ),
    Choice(
        name="Voyage".ljust(25),
        value=(ModelProviderType.VOYAGE, "Voyage", "https://api.voyageai.com/v1", "voyage-3.5"),
    ),
    Choice(
        name="Other (vLLM, ...)".ljust(25) + "🔧 provide API URL",
        value=(ModelProviderType.OTHER, "Other", ModelProviderType.OTHER, None, None),
    ),
]


async def _configure_llm() -> dict[str, str | None] | None:
    provider_type: str
    provider_name: str
    base_url: str
    recommended_model: str
    selected_model: str
    provider_type, provider_name, base_url, recommended_model = await inquirer.fuzzy(  # type: ignore
        message="Select LLM provider (type to search):", choices=LLM_PROVIDERS
    ).execute_async()

    watsonx_project_or_space: str = ""
    watsonx_project_or_space_id: str = ""

    extra_config: dict[str, str | None] = {}

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

        extra_config = {
            "watsonx_project_id": (watsonx_project_or_space_id if watsonx_project_or_space == "project" else None),
            "watsonx_space_id": (watsonx_project_or_space_id if watsonx_project_or_space == "space" else None),
        }

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
        if provider_type in {ModelProviderType.ANTHROPIC, ModelProviderType.WATSONX}:
            available_models = []
        else:
            with console.status("Loading available models...", spinner="dots"):
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{base_url}/models",
                        headers=(
                            {"RITS_API_KEY": api_key}
                            if provider_type == ModelProviderType.RITS
                            else {"Authorization": f"Bearer {api_key}"}
                        ),
                        timeout=30.0,
                    )
                    if response.status_code == 404:
                        available_models = []
                    elif response.status_code == 401:
                        console.print(
                            format_error("Error", "API key was rejected. Please check your API key and re-try.")
                        )
                        return None
                    else:
                        response.raise_for_status()
                        available_models = [m.get("id", "") for m in response.json().get("data", []) or []]
    except httpx.HTTPError as e:
        console.print(format_error("Error", str(e)))
        match provider_type:
            case ModelProviderType.OLLAMA:
                console.print("💡 [yellow]HINT[/yellow]: We could not connect to Ollama. Is it running?")
            case ModelProviderType.JAN:
                console.print(
                    "💡 [yellow]HINT[/yellow]: We could not connect to Jan. Ensure that the server is running: in the Jan application, click the [bold][<>][/bold] button and [bold]Start server[/bold]."
                )
            case ModelProviderType.OTHER:
                console.print(
                    "💡 [yellow]HINT[/yellow]: We could not connect to the API URL you have specified. Is it correct?"
                )
            case _:
                console.print(f"💡 [yellow]HINT[/yellow]: {provider_type} may be down.")
        return None

    if provider_type == ModelProviderType.OLLAMA:
        available_models = [model for model in available_models if not model.endswith("-beeai")]

    if provider_type == ModelProviderType.OLLAMA and not available_models:
        if await inquirer.confirm(  # type: ignore
            message=f"There are no locally available models in Ollama. Do you want to pull the recommended model '{recommended_model}'?",
            default=True,
        ).execute_async():
            selected_model = recommended_model
        else:
            console.print("[red]No default model configured.[/red]")
            return None
    else:
        selected_model = (
            recommended_model
            if (
                recommended_model
                and (
                    not available_models
                    or recommended_model in available_models
                    or provider_type == ModelProviderType.OLLAMA
                )
                and await inquirer.confirm(  # type: ignore
                    message=f"Do you want to use the recommended model as default '{recommended_model}'?"
                    + (
                        " It will be pulled from Ollama now."
                        if recommended_model not in available_models and provider_type == ModelProviderType.OLLAMA
                        else ""
                    ),
                    default=True,
                ).execute_async()
            )
            else (
                await inquirer.fuzzy(  # type: ignore
                    message="Select a model to be used as default (type to search):",
                    choices=sorted(available_models),
                ).execute_async()
                if available_models
                else await inquirer.text(message="Write a model name to use as default:").execute_async()  # type: ignore
            )
        )

    if provider_type == ModelProviderType.OLLAMA and selected_model not in available_models:
        try:
            await run_command(
                [_ollama_exe(), "pull", selected_model],
                "Pulling the selected model",
                check=True,
            )
        except Exception as e:
            console.print(f"[red]Error while pulling model: {e!s}[/red]")
            return None

    num_ctx: int
    if provider_type == ModelProviderType.OLLAMA and (
        (
            num_ctx := await inquirer.select(  # type: ignore
                message="Larger context window helps agents see more information at once at the cost of memory consumption, as long as the model supports it. Set a larger context window?",
                choices=[
                    Choice(name="2k    ⚠️  too small for most agents", value=2048),
                    Choice(name="4k    ⚠️  too small for most agents", value=4096),
                    Choice(name="8k", value=8192),
                    Choice(name="16k", value=16384),
                    Choice(name="32k   ⚠️  may be too large for common computers", value=32768),
                    Choice(name="64k   ⚠️  may be too large for common computers", value=65536),
                    Choice(name="128k  ⚠️  may be too large for common computers", value=131072),
                ],
            ).execute_async()
        )
        > 2048
    ):
        modified_model = f"{selected_model}-beeai"
        console.print(
            f"⚠️  [yellow]Warning[/yellow]: BeeAI will create and use a modified version of this model tagged [bold]{modified_model}[/bold] with default context window set to [bold]{num_ctx}[/bold]."
        )

        try:
            if modified_model in available_models:
                await run_command([_ollama_exe(), "rm", modified_model], "Removing old model")
            with tempfile.TemporaryDirectory() as temp_dir:
                modelfile_path = os.path.join(temp_dir, "Modelfile")
                await anyio.Path(modelfile_path).write_text(f"FROM {selected_model}\n\nPARAMETER num_ctx {num_ctx}\n")
                await run_command(
                    [_ollama_exe(), "create", modified_model],
                    "Creating modified model",
                    cwd=temp_dir,
                )
        except Exception as e:
            console.print(f"[red]Error setting up Ollama model: {e!s}[/red]")
            return None

        selected_model = modified_model

    try:
        with console.status("Checking if the model works...", spinner="dots"):
            async with httpx.AsyncClient() as client:
                test_response = await client.post(
                    (
                        f"{base_url}/ml/v1/text/chat?version=2023-10-25"
                        if provider_type == ModelProviderType.WATSONX
                        else f"{base_url}/chat/completions"
                    ),
                    json={
                        "max_tokens": 500,  # reasoning models need some tokens to think about this
                        "messages": [
                            {
                                "role": "system",
                                "content": "Repeat each message back to the user, verbatim. Don't say anything else.",
                            },
                            {"role": "user", "content": "Hello!"},
                        ],
                    }
                    | (
                        {"model_id": selected_model, f"{watsonx_project_or_space}_id": watsonx_project_or_space_id}
                        if provider_type == ModelProviderType.WATSONX
                        else {"model": selected_model}
                    ),
                    headers=(
                        {"RITS_API_KEY": api_key}
                        if provider_type == ModelProviderType.RITS
                        else {"Authorization": f"Bearer {await _get_watsonx_token(client, api_key)}"}
                        if provider_type == ModelProviderType.WATSONX
                        else {"Authorization": f"Bearer {api_key}"}
                    ),
                    timeout=30.0,
                )
        response_text = test_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        if "Hello" not in response_text:
            console.print(format_error("Error", "Model did not provide a proper response."))
            return None
    except Exception as e:
        console.print(format_error("Error", f"Error during model test: {e!s}"))
        if provider_type == ModelProviderType.OLLAMA:
            console.print(
                "💡 [yellow]HINT[/yellow]: Try setting up the model with 2k context window first, to see if it works."
            )
        if not available_models:
            console.print(
                f"💡 [yellow]HINT[/yellow]: Check {provider_type} documentation if you typed in the correct model name."
            )
        return None

    return {
        "base_url": base_url,
        "api_key": api_key,
        "name": provider_name,
        "type": provider_type,
        "default_llm_model": f"{provider_type}:{selected_model}",
        **extra_config,
    }


async def _get_watsonx_token(client: httpx.AsyncClient, api_key: str) -> str | None:
    watsonx_token_response = await client.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}",  # pyright: ignore [reportArgumentType]
        timeout=30.0,
    )
    watsonx_token_response.raise_for_status()
    return watsonx_token_response.json().get("access_token")


async def _configure_embedding(llm_env: dict[str, str | None]) -> dict[str, str | None] | None:
    base_url: str
    api_key: str
    provider_type: str
    provider_name: str
    selected_model: str
    recommended_model: str
    watsonx_project_or_space: str = ""
    watsonx_project_or_space_id: str = ""
    provider_type, provider_name, base_url, recommended_model = await inquirer.fuzzy(  # type: ignore
        message="Select embedding provider (type to search):", choices=EMBEDDING_PROVIDERS
    ).execute_async()

    extra_config: dict[str, str | None] = {}

    if provider_type == ModelProviderType.OTHER:
        base_url = await inquirer.text(  # type: ignore
            message="Enter the base URL of your embedding API (OpenAI-compatible):",
            validate=lambda url: (url.startswith(("http://", "https://")) or "URL must start with http:// or https://"),  # type: ignore
            transformer=lambda url: url.rstrip("/"),
        ).execute_async()
        if re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm\.com/.*$", base_url):
            provider_type = ModelProviderType.RITS
            if not base_url.endswith("/v1"):
                base_url = base_url.removesuffix("/") + "/v1"

    if provider_type == ModelProviderType.WATSONX:
        base_url = f"""https://{
            await inquirer.select(  # type: ignore
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
        }.ml.cloud.ibm.com"""

    if base_url == llm_env["base_url"]:
        api_key = llm_env.get("api_key") or ""
        assert api_key
        watsonx_project_or_space = "project" if "watsonx_project_id" in llm_env else "space"
        watsonx_project_or_space_id = llm_env.get("watsonx_project_id") or llm_env.get("watsonx_space_id") or ""
    else:
        if provider_type == ModelProviderType.WATSONX:
            watsonx_project_or_space = await inquirer.select(  # type: ignore
                "Use a Project or a Space?", choices=["project", "space"]
            ).execute_async()
            if (
                not (
                    watsonx_project_or_space_id := os.environ.get(f"WATSONX_{watsonx_project_or_space.upper()}_ID", "")
                )
                or not await inquirer.confirm(  # type: ignore
                    message=f"Use the {watsonx_project_or_space} id from environment variable 'WATSONX_{watsonx_project_or_space.upper()}_ID'?",
                    default=True,
                ).execute_async()
            ):
                watsonx_project_or_space_id = await inquirer.text(  # type: ignore
                    message=f"Enter the {watsonx_project_or_space} id:"
                ).execute_async()

            extra_config = {
                "watsonx_project_id": (watsonx_project_or_space_id if watsonx_project_or_space == "project" else None),
                "watsonx_space_id": (watsonx_project_or_space_id if watsonx_project_or_space == "space" else None),
            }

        if (api_key := os.environ.get(f"{provider_type.upper()}_API_KEY")) is None or not await inquirer.confirm(  # type: ignore
            message=f"Use the API key from environment variable '{provider_type.upper()}_API_KEY'?",
            default=True,
        ).execute_async():
            api_key = (
                "dummy"
                if provider_type in {ModelProviderType.OLLAMA, ModelProviderType.JAN}
                else await inquirer.secret(  # type: ignore
                    message="Enter API key for embedding:", validate=EmptyInputValidator()
                ).execute_async()
            )

    # Load available models
    try:
        if provider_type in {ModelProviderType.VOYAGE, ModelProviderType.WATSONX}:
            available_models = []
        else:
            with console.status("Loading available embedding models...", spinner="dots"):
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{base_url}/models",
                        headers=(
                            {"RITS_API_KEY": api_key}
                            if provider_type == ModelProviderType.RITS
                            else {"Authorization": f"Bearer {api_key}"}
                        ),
                        timeout=30.0,
                    )
                    if response.status_code == 404:
                        print(response.status_code, response.request.url)
                        available_models = []
                    elif response.status_code == 401:
                        console.print(
                            format_error("Error", "API key was rejected. Please check your API key and re-try.")
                        )
                        return None
                    else:
                        response.raise_for_status()
                        available_models = [m.get("id", "") for m in response.json().get("data", []) or []]
    except httpx.HTTPError as e:
        console.print(format_error("Error", str(e)))
        match provider_type:
            case ModelProviderType.OLLAMA:
                console.print("💡 [yellow]HINT[/yellow]: We could not connect to Ollama. Is it running?")
            case ModelProviderType.OTHER:
                console.print(
                    "💡 [yellow]HINT[/yellow]: We could not connect to the API URL you have specified. Is it correct?"
                )
            case _:
                console.print(f"💡 [yellow]HINT[/yellow]: {provider_type} may be down.")
        return None

    if provider_type == ModelProviderType.OLLAMA:
        available_models = [model for model in available_models if not model.endswith("-beeai")]

    if provider_type == ModelProviderType.OLLAMA and not available_models:
        if await inquirer.confirm(  # type: ignore
            message=f"There are no locally available models in Ollama. Do you want to pull the recommended embedding model '{recommended_model}'?",
            default=True,
        ).execute_async():
            selected_model = recommended_model
        else:
            console.print("[red]No embedding model configured.[/red]")
            return None
    else:
        selected_model = (
            recommended_model
            if (
                recommended_model
                and (
                    not available_models
                    or recommended_model in available_models
                    or provider_type == ModelProviderType.OLLAMA
                )
                and await inquirer.confirm(  # type: ignore
                    message=f"Do you want to use the recommended embedding model '{recommended_model}'?"
                    + (
                        " It will be pulled from Ollama now."
                        if recommended_model not in available_models and provider_type == ModelProviderType.OLLAMA
                        else ""
                    ),
                    default=True,
                ).execute_async()
            )
            else (
                await inquirer.fuzzy(  # type: ignore
                    message="Select an embedding model (type to search):",
                    choices=sorted(available_models),
                ).execute_async()
                if available_models
                else await inquirer.text(  # type: ignore
                    message=f"This provider does not provide a list of models through the API. Please manually find available models in the {provider_type} documentation and paste the name of your chosen model in the correct format here:"
                ).execute_async()
            )
        )

    if provider_type == ModelProviderType.OLLAMA and selected_model not in available_models:
        try:
            await run_command(
                [_ollama_exe(), "pull", selected_model],
                "Pulling the selected embedding model",
                check=True,
            )
        except Exception as e:
            console.print(f"[red]Error while pulling embedding model: {e!s}[/red]")
            return None

    try:
        with console.status("Checking if the model works...", spinner="dots"):
            async with httpx.AsyncClient() as client:
                test_response = await client.post(
                    (
                        f"{base_url}/ml/v1/text/embeddings?version=2024-05-02"
                        if provider_type == ModelProviderType.WATSONX
                        else f"{base_url}/embeddings"
                    ),
                    json={"input" + ("s" if provider_type == ModelProviderType.WATSONX else ""): ["Hi"]}
                    | (
                        {"model_id": selected_model, f"{watsonx_project_or_space}_id": watsonx_project_or_space_id}
                        if provider_type == ModelProviderType.WATSONX
                        else {"model": selected_model}
                    ),
                    headers=(
                        {"RITS_API_KEY": api_key}
                        if provider_type == ModelProviderType.RITS
                        else {"Authorization": f"Bearer {await _get_watsonx_token(client, api_key)}"}
                        if provider_type == ModelProviderType.WATSONX
                        else {"Authorization": f"Bearer {api_key}"}
                    ),
                    timeout=30.0,
                )
                test_response.raise_for_status()
    except Exception as e:
        console.print(format_error("Error", f"Error during model test: {e!s}"))
        return None

    return {
        "base_url": base_url,
        "api_key": api_key,
        "name": provider_name,
        "type": provider_type,
        "default_embedding_model": f"{provider_type}:{selected_model}",
        **extra_config,
    }


@app.command("setup")
async def setup(
    use_true_localhost: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    verbose: typing.Annotated[bool, typer.Option("-v")] = False,
) -> bool:
    """Interactive setup for LLM and embedding provider environment variables"""
    with verbosity(verbose):
        # Ping BeeAI platform to get an error early
        async with httpx.AsyncClient() as client:
            await client.head(str(Configuration().host))

        console.print("[bold]Setting up LLM provider...[/bold]")
        if not (llm_env := await _configure_llm()):
            return False
        embedding_env = {}
        if await inquirer.confirm(  # type: ignore
            message="Do you want to configure an embedding provider?", default=True
        ).execute_async():
            console.print("[bold]Setting up embedding provider...[/bold]")
            if not (embedding_env := await _configure_embedding(llm_env)):
                return False

        if not use_true_localhost:
            llm_env["base_url"] = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", llm_env["base_url"] or "")
            if embedding_env:
                embedding_env["base_url"] = re.sub(
                    r"localhost|127\.0\.0\.1", "host.docker.internal", embedding_env["base_url"] or ""
                )

        with console.status("Saving configuration...", spinner="dots"):
            async with configuration.use_platform_client():
                # Delete all existing providers
                for provider in await ModelProvider.list():
                    await ModelProvider.delete(provider.id)

                await ModelProvider.create(
                    name=llm_env.get("name"),
                    type=ModelProviderType(llm_env.get("type")),
                    base_url=llm_env.get("base_url"),  # pyright: ignore [reportArgumentType]
                    api_key=llm_env.get("api_key"),  # pyright: ignore [reportArgumentType]
                    watsonx_project_id=llm_env.get("watsonx_project_id"),
                    watsonx_space_id=llm_env.get("watsonx_space_id"),
                )

                if embedding_env and llm_env["base_url"] != embedding_env["base_url"]:
                    await ModelProvider.create(
                        name=embedding_env.get("name"),
                        type=ModelProviderType(embedding_env.get("type")),
                        base_url=embedding_env.get("base_url"),  # pyright: ignore [reportArgumentType]
                        api_key=embedding_env.get("api_key"),  # pyright: ignore [reportArgumentType]
                        watsonx_project_id=embedding_env.get("watsonx_project_id"),
                        watsonx_space_id=embedding_env.get("watsonx_space_id"),
                    )

                await SystemConfiguration.update(
                    default_embedding_model=embedding_env.get("default_embedding_model"),
                    default_llm_model=llm_env.get("default_llm_model"),
                )

        console.print(
            "\n[bold green]You're all set![/bold green] (You can re-run this setup anytime with [blue]beeai model setup[/blue])"
        )
        return True


async def ensure_llm_env():
    async with configuration.use_platform_client():
        config = await SystemConfiguration.get()
        default_model = config.default_llm_model
        providers = await ModelProvider.list()
        if default_model and providers:
            return
    console.print("[bold]Welcome to 🐝 [red]BeeAI[/red]![/bold]")
    console.print("Let's start by configuring your LLM environment.\n")
    if not await setup():
        console.print(format_error("Error", "Could not continue because the LLM environment is not properly set up."))
        console.print(
            "💡 [yellow]HINT[/yellow]: Try re-entering your LLM API details with: [green]beeai model setup[/green]"
        )
        sys.exit(1)
    console.print()
