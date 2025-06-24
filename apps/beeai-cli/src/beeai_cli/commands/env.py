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


import os
import re
import sys
import tempfile
import typing

import anyio
import httpx
import typer
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator
from rich.table import Column

from beeai_cli.api import api_request
from beeai_cli.async_typer import AsyncTyper, console, create_table, err_console
from beeai_cli.configuration import Configuration
from beeai_cli.utils import format_error, parse_env_var, run_command, verbosity

app = AsyncTyper()


@app.command("add")
async def add(
    env: typing.Annotated[list[str], typer.Argument(help="Environment variables to pass to agent")],
) -> None:
    """Store environment variables"""
    env_vars = dict(parse_env_var(var) for var in env)
    await api_request(
        "put",
        "variables",
        json={**({"env": env_vars} if env_vars else {})},
    )
    await list_env()


@app.command("list")
async def list_env():
    """List stored environment variables"""
    # TODO: extract server schemas to a separate package
    resp = await api_request("get", "variables")
    with create_table(Column("name", style="yellow"), Column("value", ratio=1)) as table:
        for name, value in sorted(resp["env"].items()):
            table.add_row(name, value)
    console.print(table)


@app.command("remove")
async def remove_env(
    env: typing.Annotated[list[str], typer.Argument(help="Environment variable(s) to remove")],
):
    await api_request("put", "variables", json={**({"env": dict.fromkeys(env)})})
    await list_env()


@app.command("setup", help="Interactive setup for LLM provider environment variables")
async def setup(
    use_true_localhost: typing.Annotated[bool, typer.Option(hidden=True)] = False,
    verbose: typing.Annotated[bool, typer.Option("-v")] = False,
) -> bool:
    """Interactive setup for LLM provider environment variables"""
    with verbosity(verbose):
        # Ping BeeAI platform to get an error early
        async with httpx.AsyncClient() as client:
            await client.head(str(Configuration().host))

        provider_name, api_base, recommended_model = await inquirer.fuzzy(
            message="Select LLM provider (type to search):",
            choices=[
                Choice(
                    name="Anthropic Claude".ljust(25),
                    value=("Anthropic", "https://api.anthropic.com/v1", "claude-3-7-sonnet-latest"),
                ),
                Choice(
                    name="Cerebras".ljust(25) + "🆓 has a free tier",
                    value=("Cerebras", "https://api.cerebras.ai/v1", "llama-3.3-70b"),
                ),
                Choice(
                    name="Chutes".ljust(25) + "🆓 has a free tier",
                    value=("Chutes", "https://llm.chutes.ai/v1/", None),
                ),
                Choice(
                    name="Cohere".ljust(25) + "🆓 has a free tier",
                    value=("Cohere", "https://api.cohere.ai/compatibility/v1", "command-r-plus"),
                ),
                Choice(
                    name="DeepSeek",
                    value=("DeepSeek", "https://api.deepseek.com/v1", "deepseek-reasoner"),
                ),
                Choice(
                    name="Google Gemini".ljust(25) + "🆓 has a free tier",
                    value=("Google", "https://generativelanguage.googleapis.com/v1beta/openai/", None),
                ),
                Choice(
                    name="Groq".ljust(25) + "🆓 has a free tier",
                    value=("Groq", "https://api.groq.com/openai/v1", "deepseek-r1-distill-llama-70b"),
                ),
                Choice(
                    name="IBM watsonx".ljust(25),
                    value=("watsonx", None, "ibm/granite-3-3-8b-instruct"),
                ),
                Choice(name="Jan".ljust(25) + "💻 local", value=("Jan", "http://localhost:1337/v1", None)),
                Choice(
                    name="Mistral".ljust(25) + "🆓 has a free tier",
                    value=("Mistral", "https://api.mistral.ai/v1", "mistral-large-latest"),
                ),
                Choice(
                    name="NVIDIA NIM".ljust(25),
                    value=("NVIDIA", "https://integrate.api.nvidia.com/v1", "deepseek-ai/deepseek-r1"),
                ),
                Choice(
                    name="Ollama".ljust(25) + "💻 local", value=("Ollama", "http://localhost:11434/v1", "granite3.3:8b")
                ),
                Choice(
                    name="OpenAI".ljust(25),
                    value=("OpenAI", "https://api.openai.com/v1", "gpt-4o"),
                ),
                Choice(
                    name="OpenRouter".ljust(25) + "🆓 has some free models",
                    value=("OpenRouter", "https://openrouter.ai/api/v1", "deepseek/deepseek-r1-distill-llama-70b:free"),
                ),
                Choice(name="Perplexity".ljust(25), value=("Perplexity", "https://api.perplexity.ai", None)),
                Choice(
                    name="together.ai".ljust(25) + "🆓 has a free tier",
                    value=("Together", "https://api.together.xyz/v1", "deepseek-ai/DeepSeek-R1"),
                ),
                Choice(name="Other (RITS, vLLM, ...)".ljust(25) + "🔧 provide API URL", value=("Other", None, None)),
            ],
        ).execute_async()

        if provider_name == "Other":
            api_base = await inquirer.text(
                message="Enter the base URL of your API (OpenAI-compatible):",
                validate=lambda url: (
                    url.startswith(("http://", "https://")) or "URL must start with http:// or https://"
                ),
                transformer=lambda url: url.rstrip("/"),
            ).execute_async()
            if re.match(r"^https://[a-z0-9.-]+\.rits\.fmaas\.res\.ibm\.com/.*$", api_base):
                provider_name = "RITS"
                if not api_base.endswith("/v1"):
                    api_base = api_base.removesuffix("/") + "/v1"

        if provider_name == "watsonx":
            api_base = f"""https://{
                await inquirer.select(
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
            watsonx_project_or_space = await inquirer.select(
                "Use a Project or a Space?", choices=["project", "space"]
            ).execute_async()
            watsonx_project_or_space_id = await inquirer.text(
                message=f"Enter the {watsonx_project_or_space} id:"
            ).execute_async()

        if (api_key := os.environ.get(f"{provider_name.upper()}_API_KEY")) is None or not await inquirer.confirm(
            message=f"Use the API key from environment variable '{provider_name.upper()}_API_KEY'?",
            default=True,
        ).execute_async():
            api_key = (
                "dummy"
                if provider_name in ["Ollama", "Jan"]
                else await inquirer.secret(message="Enter API key:", validate=EmptyInputValidator()).execute_async()
            )

        try:
            if provider_name in ["Anthropic", "watsonx"]:
                available_models = []
            else:
                with console.status("Loading available models...", spinner="dots"):
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{api_base}/models",
                            headers=(
                                {"RITS_API_KEY": api_key}
                                if provider_name == "RITS"
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
                            return False
                        else:
                            response.raise_for_status()
                            available_models = [m.get("id", "") for m in response.json().get("data", []) or []]
        except httpx.HTTPError as e:
            console.print(format_error("Error", str(e)))
            match provider_name:
                case "Ollama":
                    console.print("💡 [yellow]HINT[/yellow]: We could not connect to Ollama. Is it running?")
                case "Jan":
                    console.print(
                        "💡 [yellow]HINT[/yellow]: We could not connect to Jan. Ensure that the server is running: in the Jan application, click the [bold][<>][/bold] button and [bold]Start server[/bold]."
                    )
                case "Other":
                    console.print(
                        "💡 [yellow]HINT[/yellow]: We could not connect to the API URL you have specified. Is it correct?"
                    )
                case _:
                    console.print(f"💡 [yellow]HINT[/yellow]: {provider_name} may be down.")
            return False

        if provider_name == "Ollama":
            available_models = [model for model in available_models if not model.endswith("-beeai")]

        if provider_name == "Ollama" and not available_models:
            if await inquirer.confirm(
                message=f"There are no locally available models in Ollama. Do you want to pull the recommended model '{recommended_model}'?",
                default=True,
            ).execute_async():
                selected_model = recommended_model
            else:
                console.print("[red]No model configured.[/red]")
                return False
        else:
            selected_model = (
                recommended_model
                if (
                    recommended_model
                    and (not available_models or recommended_model in available_models or provider_name == "Ollama")
                    and await inquirer.confirm(
                        message=f"Do you want to use the recommended model '{recommended_model}'?"
                        + (
                            " It will be pulled from Ollama now."
                            if recommended_model not in available_models and provider_name == "Ollama"
                            else ""
                        ),
                        default=True,
                    ).execute_async()
                )
                else (
                    await inquirer.fuzzy(
                        message="Select a model (type to search):",
                        choices=sorted(available_models),
                    ).execute_async()
                    if available_models and len(available_models) > 1
                    else available_models[0]
                    if available_models and len(available_models) == 1
                    else await inquirer.text(message="Write a model name to use:").execute_async()
                )
            )

        if provider_name == "Ollama" and selected_model not in available_models:
            try:
                await run_command(
                    ["ollama", "pull", selected_model],
                    "Pulling the selected model",
                    check=True,
                )
            except Exception as e:
                console.print(f"[red]Error while pulling model: {e!s}[/red]")
                return False

        if provider_name == "Ollama" and (
            (
                num_ctx := await inquirer.select(
                    message="Larger context window helps agents see more information at once at the cost of memory consumption, as long as the model supports it. Set a larger context window?",
                    choices=[
                        Choice(name="2k  ⚠️  some agents won't work", value=2048),
                        Choice(name="4k  ⚠️  some agents won't work", value=4096),
                        Choice(name="8k", value=8192),
                        Choice(name="16k", value=16384),
                        Choice(name="32k", value=32768),
                        Choice(name="64k", value=65536),
                        Choice(name="128k", value=131072),
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
                    await run_command(["ollama", "rm", modified_model], "Removing old model")
                with tempfile.TemporaryDirectory() as temp_dir:
                    modelfile_path = os.path.join(temp_dir, "Modelfile")
                    await anyio.Path(modelfile_path).write_text(
                        f"FROM {selected_model}\n\nPARAMETER num_ctx {num_ctx}\n"
                    )
                    await run_command(
                        ["ollama", "create", modified_model],
                        "Creating modified model",
                        cwd=temp_dir,
                    )
            except Exception as e:
                console.print(f"[red]Error setting up Ollama model: {e!s}[/red]")
                return False

            selected_model = modified_model

        try:
            with console.status("Checking if the model works...", spinner="dots"):
                async with httpx.AsyncClient() as client:
                    if provider_name == "watsonx":
                        watsonx_token_response = await client.post(
                            "https://iam.cloud.ibm.com/identity/token",
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                            data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}",
                            timeout=30.0,
                        )
                        watsonx_token_response.raise_for_status()
                        watsonx_access_token = watsonx_token_response.json().get("access_token")
                    test_response = await client.post(
                        (
                            f"{api_base}/ml/v1/text/chat?version=2023-10-25"
                            if provider_name == "watsonx"
                            else f"{api_base}/chat/completions"
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
                            if provider_name == "watsonx"
                            else {"model": selected_model}
                        ),
                        headers=(
                            {"RITS_API_KEY": api_key}
                            if provider_name == "RITS"
                            else {"Authorization": f"Bearer {watsonx_access_token}"}
                            if provider_name == "watsonx"
                            else {"Authorization": f"Bearer {api_key}"}
                        ),
                        timeout=30.0,
                    )
            response_text = test_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if "Hello" not in response_text:
                err_console.print(format_error("Error", "Model did not provide a proper response."))
                return False
        except Exception as e:
            err_console.print(format_error("Error", f"Error during model test: {e!s}"))
            return False

        if not use_true_localhost:
            api_base = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", api_base)

        with console.status("Saving configuration...", spinner="dots"):
            await api_request(
                "put",
                "variables",
                json={
                    "env": {
                        # Replace localhost by host.lima.internal for lima
                        "LLM_API_BASE": api_base,
                        "LLM_API_KEY": api_key,
                        "LLM_MODEL": selected_model,
                        "WATSONX_PROJECT_ID": (
                            watsonx_project_or_space_id
                            if provider_name == "watsonx" and watsonx_project_or_space == "project"
                            else None
                        ),
                        "WATSONX_SPACE_ID": (
                            watsonx_project_or_space_id
                            if provider_name == "watsonx" and watsonx_project_or_space == "space"
                            else None
                        ),
                    }
                },
            )

        console.print(
            "\n[bold green]You're all set![/bold green] (You can re-run this setup anytime with [blue]beeai env setup[/blue])"
        )
        return True


async def ensure_llm_env():
    try:
        env = (await api_request("get", "variables"))["env"]
    except httpx.HTTPStatusError:
        return  # Skip for non-conforming servers (like when running directly against an agent provider)
    if all(required_variable in env for required_variable in ["LLM_MODEL", "LLM_API_KEY", "LLM_API_BASE"]):
        return
    console.print("[bold]Welcome to 🐝 [red]BeeAI[/red]![/bold]")
    console.print("Let's start by configuring your LLM environment.\n")
    if not await setup():
        err_console.print(
            format_error("Error", "Could not continue because the LLM environment is not properly set up.")
        )
        err_console.print(
            "💡 [yellow]HINT[/yellow]: Try re-entering your LLM API details with: [green]beeai env setup[/green]"
        )
        sys.exit(1)
    console.print()
