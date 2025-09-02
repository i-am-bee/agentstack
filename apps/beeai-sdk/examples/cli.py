# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

# Based on: https://github.com/a2aproject/a2a-samples/tree/main/samples/python/hosts/cli

import asyncio
import base64
import os
import uuid

import a2a.client
import a2a.types
import anyio
import asyncclick
import asyncclick.exceptions
import httpx
import yaml
from pydantic import AnyHttpUrl

import beeai_sdk.a2a.extensions.services.llm


@asyncclick.command()
@asyncclick.option("--base-url", default="http://127.0.0.1:10000")
@asyncclick.option("--context-id", default="")
async def cli(base_url: str, context_id: str) -> None:
    async with httpx.AsyncClient(timeout=30) as httpx_client:
        card = await a2a.client.A2ACardResolver(httpx_client, base_url=base_url).get_agent_card()

        print("======= Agent Card ========")
        print(yaml.dump(card.model_dump(mode="json", exclude_none=True)))

        client = a2a.client.ClientFactory(a2a.client.ClientConfig(httpx_client=httpx_client, polling=True)).create(card)
        context_id = context_id or uuid.uuid4().hex

        llm_spec = beeai_sdk.a2a.extensions.LLMServiceExtensionSpec.from_agent_card(card)
        mcp_spec = beeai_sdk.a2a.extensions.MCPServiceExtensionSpec.from_agent_card(card)
        trajectory_spec = beeai_sdk.a2a.extensions.TrajectoryExtensionSpec.from_agent_card(card)
        trajectory_client = (
            beeai_sdk.a2a.extensions.TrajectoryExtensionClient(trajectory_spec) if trajectory_spec else None
        )

        while True:
            print("\n\n=========  starting a new task ======== ")

            task: a2a.types.Task | None = None
            try:
                no_task = False
                while not no_task and (
                    not task
                    or task.status.state
                    in [
                        a2a.types.TaskState.input_required,
                        a2a.types.TaskState.auth_required,
                    ]
                ):
                    prompt: str = asyncclick.prompt("\n👤 User (CTRL-D to cancel)")

                    message = a2a.types.Message(
                        message_id=str(uuid.uuid4()),
                        role=a2a.types.Role.user,
                        parts=[a2a.types.Part(root=a2a.types.TextPart(text=prompt))],
                        task_id=task and task.id,
                        context_id=context_id,
                        metadata=(
                            beeai_sdk.a2a.extensions.LLMServiceExtensionClient(llm_spec).fulfillment_metadata(
                                llm_fulfillments={
                                    # Demonstration only: we ignore the asks and just configure BeeAI proxy for everything
                                    key: beeai_sdk.a2a.extensions.services.llm.LLMFulfillment(
                                        api_base="http://localhost:8333/api/v1/llm/",
                                        api_key="dummy",
                                        api_model="dummy",
                                    )
                                    for key in llm_spec.params.llm_demands
                                }
                            )
                            if llm_spec
                            else {}
                        )
                        | (
                            beeai_sdk.a2a.extensions.MCPServiceExtensionClient(mcp_spec).fulfillment_metadata(
                                mcp_fulfillments={
                                    # Demonstration only: we ignore the asks and just configure BeeAI proxy for everything
                                    key: beeai_sdk.a2a.extensions.services.mcp.MCPFulfillment(
                                        transport=beeai_sdk.a2a.extensions.services.mcp.StreamableHTTPTransport(
                                            url=AnyHttpUrl("http://localhost:8333/mcp"),
                                        ),
                                    )
                                    for key in mcp_spec.params.mcp_demands
                                }
                            )
                            if mcp_spec
                            else {}
                        ),
                    )

                    file_path: str = asyncclick.prompt(
                        "Select a file path to attach? (press enter to skip)",
                        default="",
                        show_default=False,
                    )

                    print("🤖 Agent: ")

                    if file_path and file_path.strip() != "":
                        message.parts.append(
                            a2a.types.Part(
                                root=a2a.types.FilePart(
                                    file=a2a.types.FileWithBytes(
                                        name=os.path.basename(file_path),
                                        bytes=base64.b64encode(await anyio.Path(file_path).read_bytes()).decode(
                                            "utf-8"
                                        ),
                                    )
                                )
                            )
                        )

                    printing_streaming_tokens = False
                    async for event in client.send_message(message):
                        if isinstance(event, a2a.types.Message):
                            no_task = True
                            print(f"MESSAGE => {event.model_dump_json(exclude_none=True)}")
                            continue

                        task, update = event
                        if task.context_id:
                            context_id = task.context_id

                        if isinstance(update, a2a.types.TaskArtifactUpdateEvent):
                            if printing_streaming_tokens:
                                print()
                                printing_streaming_tokens = False
                            print(f"ARTIFACT => {update.model_dump_json(exclude_none=True)}")
                        elif isinstance(update, a2a.types.TaskStatusUpdateEvent):
                            if update.status.message:
                                if not printing_streaming_tokens:
                                    print()
                                    printing_streaming_tokens = True
                                for part in update.status.message.parts:
                                    if isinstance(part.root, a2a.types.TextPart):
                                        print(part.root.text, end="", flush=True)
                                if trajectory_client and (
                                    trajectory := trajectory_client.parse_server_metadata(update.status.message)
                                ):
                                    print(trajectory.model_dump())
                        else:
                            if printing_streaming_tokens:
                                print()
                                printing_streaming_tokens = False
                            print(f"TASK => {task.model_dump_json(exclude_none=True)}")
            except asyncclick.exceptions.Abort:
                print("Exiting...")
                return
            finally:
                if task and task.status.state not in [
                    a2a.types.TaskState.completed,
                    a2a.types.TaskState.failed,
                    a2a.types.TaskState.canceled,
                ]:
                    await client.cancel_task(a2a.types.TaskIdParams(id=task.id))
                    print(f"TASK => {task.model_dump_json(exclude_none=True)}")


if __name__ == "__main__":
    try:
        asyncio.run(cli())
    except KeyboardInterrupt:
        print("Exiting...")
