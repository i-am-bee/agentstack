# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from typing import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState, TextPart
from a2a.utils import new_task


class FinalAgentExecutor(AgentExecutor):
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancelling is not implemented")

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task = new_task(context.message)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        # Standard text
        await updater.update_status(
            state=TaskState.working,
            message=updater.new_agent_message(
                parts=[Part(root=TextPart(text="If you are bored, you can try tipping a cow."))],
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
