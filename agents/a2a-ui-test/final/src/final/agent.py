# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState, TextPart, FilePart, FileWithUri
from a2a.utils import new_task
from httpx import AsyncClient


class FinalAgentExecutor(AgentExecutor):
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancelling is not implemented")

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task = new_task(context.message)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        # Files
        for part in context.message.parts:
            if part.root.kind == "file":
                url = part.root.file.uri.replace("{platform_url}", "localhost:3000")
                async with AsyncClient() as client:
                    response = await client.get(url)
                    upload_response = await client.post(
                        "http://localhost:3000/api/v1/files",
                        files={"file": ("recreated.txt", response.text, "text/plain")},
                    )

                    await updater.update_status(
                        state=TaskState.working,
                        message=updater.new_agent_message(
                            parts=[
                                Part(
                                    root=FilePart(
                                        file=FileWithUri(
                                            uri="http://localhost:3000/api/v1/files/"
                                            + upload_response.json()['id'],
                                            name="recreated.txt",
                                            mimeType="text/plain",
                                        )
                                    )
                                )
                            ]
                        ),
                    )

        # Standard text
        await updater.update_status(
            state=TaskState.working,
            message=updater.new_agent_message(
                parts=[
                    Part(
                        root=TextPart(
                            text="If you are bored, you can try tipping a cow."
                        )
                    )
                ],
            ),
        )
        # Trajectory Message
        await updater.update_status(
            state=TaskState.working,
            message=updater.new_agent_message(
                parts=[
                    Part(
                        root=TextPart(
                            text="",
                            metadata={
                                "https://a2a-extensions.beeai.dev/trajectory/v1": {
                                    "message": "Thinking about the weather in San Francisco, CA",
                                }
                            },
                        )
                    )
                ],
            ),
        )

        # Trajectory Tool
        await updater.update_status(
            state=TaskState.working,
            message=updater.new_agent_message(
                parts=[
                    Part(
                        root=TextPart(
                            text="",
                            metadata={
                                "https://a2a-extensions.beeai.dev/trajectory/v1": {
                                    "message": "Calling weather_api",
                                    "tool_name": "weather_api",
                                    "tool_input": {"location": "San Francisco, CA"},
                                    "tool_output": {
                                        "temperature": 72,
                                        "condition": "sunny",
                                    },
                                }
                            },
                        )
                    )
                ],
            ),
        )

        # Citation
        await updater.update_status(
            state=TaskState.working,
            message=updater.new_agent_message(
                parts=[
                    Part(
                        root=TextPart(
                            text="",
                            metadata={
                                "https://a2a-extensions.beeai.dev/citations/v1": {
                                    "url": "https://en.wikipedia.org/wiki/Cow_tipping",
                                    "start_index": 30,
                                    "end_index": 43,
                                    "title": "Cow Tipping",
                                    "description": "Cow Tipping is a sport where people tip cows over.",
                                }
                            },
                        )
                    )
                ],
            ),
        )

        await updater.complete()
