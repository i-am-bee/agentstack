# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import io
import subprocess
import os
import sys
import tempfile
from pathlib import Path
from collections.abc import AsyncGenerator
from textwrap import dedent

from acp_sdk.models.platform import PlatformUIAnnotation, PlatformUIType
from acp_sdk import Annotations, Message, Metadata, Link, LinkType, MessagePart, Artifact
from acp_sdk.server import Context, Server
from pydantic import AnyUrl
import mimetypes

server = Server()


@server.agent(
    input_content_types=["none"],
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                user_greeting="Define your programming task.",
                display_name="Aider",
            ),
        ),
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/community/aider"
                ),
            )
        ],
        license="Apache 2.0",
        framework="Custom",
        documentation=dedent(
            """\
            > ℹ️ NOTE
            > 
            > This agent works in stateless mode at the moment. While the CLI only shows the textual output, the created files are also available through the API.

            The agent is an advanced AI pair programming assistant designed to help developers edit and manage code in their local git repositories via natural language instructions. It leverages AI to assist programmers in writing, editing, debugging, and understanding code, enhancing productivity and simplifying complex coding tasks. The agent runs in a local environment and interacts directly with the user's codebase, providing actionable insights and modifications.

            ## How It Works
            The agent operates as a server-based application that listens for programming-related commands. Upon receiving a command in natural language, it executes the appropriate actions within a temporary directory, simulating changes and returning feedback to the user. The agent uses subprocess execution to run the `aider` command with various options, capturing both standard output and errors to provide detailed responses. It also reads files generated during the process to include their content in the output if applicable.

            ## Input Parameters
            The agent requires the following input parameters:
            - **input** (string) – The prompt containing natural language instructions for code editing or management.

            ## Output Structure
            The agent returns an `Output` object with the following fields:
            - **files** (dict) – A dictionary mapping file paths to their respective content, representing any new or modified files.
            - **text** (str) – A string containing the text output from the executed commands, including any error messages.

            ## Key Features
            - **Natural Language Processing** – Understands and executes code-related commands described in natural language.
            - **Local Environment Integration** – Operates directly within the user's local environment, simulating changes in a temporary workspace.
            - **Real-Time Feedback** – Provides continuous updates on the execution progress and returns detailed results.
            - **Error Handling** – Captures and reports errors encountered during execution, assisting with debugging.
            """
        ),
        use_cases=[
            "**Program Generation from Natural Language** – Converts user requests into fully functional programs.",
            "**Code Editing and Refactoring** – Assists developers in modifying existing codebases without manual intervention.",
            "**Debugging Support** – Provides insights and suggestions for resolving coding errors or inefficiencies.",
            "**Collaborative Programming** – Simulates a pair programming experience, enhancing coding efficiency and learning.",
            "**Bash/Shell Scripting Assistance** – Automates script writing, optimization, and debugging.",
        ],
        env=[
            {
                "name": "LLM_MODEL",
                "required": False,
                "description": "Model to use from the specified OpenAI-compatible API.",
            },
            {"name": "LLM_API_BASE", "required": False, "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "required": False, "description": "API key for OpenAI-compatible API endpoint"},
            {
                "name": "AIDER_REASONING_EFFORT",
                "required": False,
                "description": "Set the reasoning_effort API parameter for the model",
            },
            {
                "name": "AIDER_VERIFY_SSL",
                "required": False,
                "description": "Verify the SSL cert when connecting to models (default: True)",
            },
            {
                "name": "AIDER_ARCHITECT",
                "required": False,
                "description": "Use architect edit format for the main chat",
            },
            {
                "name": "AIDER_WEAK_MODEL",
                "required": False,
                "description": "Specify the model to use for commit messages and chat history summarization (default depends on --model)",
            },
            {
                "name": "AIDER_EDITOR_MODEL",
                "required": False,
                "description": "Specify the model to use for editor tasks (default depends on model)",
            },
            {
                "name": "AIDER_EDITOR_EDIT_FORMAT",
                "required": False,
                "description": "Specify the edit format for the editor model (default: depends on editor model)",
            },
            {
                "name": "AIDER_MAX_CHAT_HISTORY_TOKENS",
                "required": False,
                "description": "Soft limit on tokens for chat history, after which summarization begins. If unspecified, defaults to the model's max_chat_history_tokens",
            },
            {
                "name": "AIDER_CACHE_PROMPTS",
                "required": False,
                "description": "Enable caching of prompts (default: False)",
            },
            {
                "name": "AIDER_CACHE_KEEPALIVE_PINGS",
                "required": False,
                "description": "Number of times to ping at 5min intervals to keep prompt cache warm (default: 0)",
            },
            {
                "name": "AIDER_MAP_TOKENS",
                "required": False,
                "description": "Suggested number of tokens to use for repo map, use 0 to disable",
            },
            {
                "name": "AIDER_MAP_REFRESH",
                "required": False,
                "description": "Control how often the repo map is refreshed. Options: auto, always, files, manual (default: auto)",
            },
            {
                "name": "AIDER_MAP_MULTIPLIER_NO_FILES",
                "required": False,
                "description": "Multiplier for map tokens when no files are specified (default: 2)",
            },
        ],
    ),
)
async def aider(input: list[Message], context: Context) -> AsyncGenerator:
    """
    An AI pair programmer that edits code in a local Git repository using natural language, executing commands and providing feedback.
    """
    user_message = str(input[-1])
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = env.get("LLM_API_KEY", "dummy")
            env["OPENAI_API_BASE"] = env.get("LLM_API_BASE", "http://localhost:11434/v1")
            env["AIDER_MODEL"] = f"openai/{env.get('LLM_MODEL', 'llama3.1')}"
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "aider",
                "--yes",
                "--no-auto-commits",
                "--no-git",
                "--no-pretty",
                "--no-analytics",
                "--no-restore-chat-history",
                "--no-show-model-warnings",
                "--no-show-release-notes",
                "--no-detect-urls",
                "--no-auto-lint",
                "--no-auto-test",
                "--no-check-update",
                "--message",
                user_message,
                cwd=tmp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            binary_buffer = io.BytesIO()
            string_reader = io.TextIOWrapper(buffer=binary_buffer, encoding="utf-8", errors="ignore")
            while True:
                chunk = await process.stdout.read(1024)
                if not chunk:
                    break
                binary_buffer_position = binary_buffer.tell()
                binary_buffer.write(chunk)
                binary_buffer.seek(binary_buffer_position)
                text_chunk = string_reader.read()
                if text_chunk:
                    yield MessagePart(content=text_chunk, role="assistant")

            stderr_bytes = await process.stderr.read()
            await process.wait()

            if process.returncode != 0:
                error_text = stderr_bytes.decode(errors="ignore") if stderr_bytes else "Unknown error occurred"
                yield MessagePart(content=f"\nAider process failed with error:\n{error_text}", role="assistant")
                return

            for file_path in tmp_path.rglob("*"):
                if any(
                    part in [".git", "node_modules", ".venv"] or part.startswith(".aider.") for part in file_path.parts
                ):
                    continue
                if file_path.is_file():
                    try:
                        content = file_path.read_bytes()
                        relative_path = str(file_path.relative_to(tmp_path))
                        content_type, _ = mimetypes.guess_type(relative_path)
                        yield Artifact(
                            name=relative_path, content=content, content_type=content_type or "application/octet-stream"
                        )
                    except Exception as e:
                        yield MessagePart(
                            content=f"Error reading file {file_path.relative_to(tmp_path)}: {str(e)}", role="assistant"
                        )

        except Exception as e:
            yield MessagePart(content=f"An unexpected error occurred: {str(e)}", role="assistant")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))
