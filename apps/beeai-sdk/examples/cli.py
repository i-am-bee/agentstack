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

import beeai_sdk.a2a_extensions.services.llm


@asyncclick.command()
@asyncclick.option("--base-url", default="http://127.0.0.1:10000")
@asyncclick.option("--context-id", default="")
@asyncclick.option("--history", default=False)
async def cli(base_url: str, context_id: str, history: bool) -> None:
    async with httpx.AsyncClient(timeout=30) as httpx_client:
        card = await a2a.client.A2ACardResolver(httpx_client, base_url=base_url).get_agent_card()

        print("======= Agent Card ========")
        print(yaml.dump(card.model_dump(mode="json", exclude_none=True)))

        client = a2a.client.A2AClient(httpx_client, agent_card=card)
        context_id = context_id or uuid.uuid4().hex

        llm_service_extension = beeai_sdk.a2a_extensions.services.llm.LLMServiceExtension.from_agent_card(card)

        while True:
            print("\n\n=========  starting a new task ======== ")
            task_id = None

            while True:
                try:
                    prompt: str = asyncclick.prompt("\n👤 User (CTRL-D to cancel)")
                except asyncclick.exceptions.Abort:
                    print("Exiting...")
                    return

                message = a2a.types.Message(
                    message_id=str(uuid.uuid4()),
                    role=a2a.types.Role.user,
                    parts=[a2a.types.Part(root=a2a.types.TextPart(text=prompt))],
                    task_id=task_id,
                    context_id=context_id,
                    metadata=llm_service_extension.build_message_metadata(
                        llm_fulfillments={
                            # Demonstration only: we ignore the asks and just configure BeeAI proxy for everything
                            key: beeai_sdk.a2a_extensions.services.llm.LLMFulfillment(
                                api_base="http://localhost:8333/api/v1/llm/",
                                api_key="dummy",
                                api_model="dummy",
                            )
                            for key in llm_service_extension.llm_demands
                        }
                    )
                    if llm_service_extension
                    else None,
                )

                try:
                    file_path: str = asyncclick.prompt(
                        "Select a file path to attach? (press enter to skip)",
                        default="",
                        show_default=False,
                    )
                except asyncclick.exceptions.Abort:
                    print("Exiting...")
                    return

                print("🤖 Agent: ")

                if file_path and file_path.strip() != "":
                    message.parts.append(
                        a2a.types.Part(
                            root=a2a.types.FilePart(
                                file=a2a.types.FileWithBytes(
                                    name=os.path.basename(file_path),
                                    bytes=base64.b64encode(await anyio.Path(file_path).read_bytes()).decode("utf-8"),
                                )
                            )
                        )
                    )

                payload = a2a.types.MessageSendParams(
                    message=message,
                    configuration=a2a.types.MessageSendConfiguration(
                        accepted_output_modes=["text"],
                    ),
                )

                task_result = None
                message_result = None
                task_completed = False

                if card.capabilities.streaming:
                    response_stream = client.send_message_streaming(
                        a2a.types.SendStreamingMessageRequest(
                            id=str(uuid.uuid4()),
                            params=payload,
                        )
                    )
                    printing_streaming_tokens = False
                    async for result in response_stream:
                        if isinstance(result.root, a2a.types.JSONRPCErrorResponse):
                            if printing_streaming_tokens:
                                print()
                            print(f"Error: {result.root.error}, context_id: {context_id}, task_id: {task_id}")
                            return

                        event = result.root.result
                        if event.context_id:
                            context_id = event.context_id

                        if isinstance(event, a2a.types.Task):
                            task_id = event.id
                            if printing_streaming_tokens:
                                print()
                                printing_streaming_tokens = False
                            print(f"TASK => {event.model_dump_json(exclude_none=True)}")
                        elif isinstance(event, a2a.types.TaskArtifactUpdateEvent):
                            task_id = event.task_id
                            if printing_streaming_tokens:
                                print()
                                printing_streaming_tokens = False
                            print(f"ARTIFACT => {event.model_dump_json(exclude_none=True)}")
                        elif isinstance(event, a2a.types.TaskStatusUpdateEvent):
                            task_id = event.task_id
                            if event.status.message:
                                if not printing_streaming_tokens:
                                    print()
                                    printing_streaming_tokens = True
                                for part in event.status.message.parts:
                                    if isinstance(part.root, a2a.types.TextPart):
                                        print(part.root.text, end="", flush=True)
                            if event.status.state == "completed":
                                task_completed = True
                        else:
                            message_result = event

                    if task_id and not task_completed:
                        task_result_response = await client.get_task(
                            a2a.types.GetTaskRequest(
                                id=str(uuid.uuid4()),
                                params=a2a.types.TaskQueryParams(id=task_id),
                            )
                        )
                        if isinstance(task_result_response.root, a2a.types.JSONRPCErrorResponse):
                            print(
                                f"Error: {task_result_response.root.error}, context_id: {context_id}, task_id: {task_id}"
                            )
                            return
                        task_result = task_result_response.root.result
                else:
                    try:
                        event = (
                            await client.send_message(
                                a2a.types.SendMessageRequest(
                                    id=str(uuid.uuid4()),
                                    params=payload,
                                )
                            )
                        ).root.result
                        if not context_id and event and event.context_id:
                            context_id = event.context_id
                        if isinstance(event, a2a.types.Task):
                            if not task_id:
                                task_id = event.id
                            task_result = event
                        elif isinstance(event, a2a.types.Message):
                            message_result = event
                    except Exception as e:
                        print("Failed to complete the call", e)

                if message_result:
                    print(f"\n{message_result.model_dump_json(exclude_none=True)}")
                    break

                if task_result:
                    task_content = task_result.model_dump_json(
                        exclude={
                            "history": {
                                "__all__": {
                                    "parts": {
                                        "__all__": {"file"},
                                    },
                                },
                            },
                        },
                        exclude_none=True,
                    )
                    print(f"\n{task_content}")

                    state = a2a.types.TaskState(task_result.status.state)
                    if state.name == a2a.types.TaskState.input_required.name:
                        continue
                    else:
                        break

                break

            if history and task_id:
                print("========= history ======== ")
                task_response = await client.get_task(
                    a2a.types.GetTaskRequest(
                        id=str(uuid.uuid4()), params=a2a.types.TaskQueryParams(id=task_id, history_length=10)
                    )
                )
                print(task_response.model_dump_json(include={"result": {"history": True}}))


if __name__ == "__main__":
    try:
        asyncio.run(cli())
    except KeyboardInterrupt:
        print("Exiting...")
