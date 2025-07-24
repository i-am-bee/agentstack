# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import AsyncGenerator, Callable
import uuid
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    TaskState,
    Role,
    Part,
    TextPart as A2ATextPart,
    Message as A2AMessage,
)
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.utils import new_task
from a2a.server.tasks import TaskUpdater
from fastapi.middleware.cors import CORSMiddleware


from models import TextPart

from extensions import BeeAIUI


class RunnableAgent(AgentCard):
    @abc.abstractmethod
    def run(self, input: list[TextPart]) -> AsyncGenerator[TextPart, str]:
        pass


def agent_decorator(
    name: str | None = None,
    description: str | None = None,
    input_content_types: list[str] | None = None,
    output_content_types: list[str] | None = None,
    ui: BeeAIUI | None = None,
) -> Callable[[Callable], RunnableAgent]:
    def decorator(fn: Callable) -> RunnableAgent:
        class DecoratedAgent(RunnableAgent):
            def run(self, input: list[str]) -> AsyncGenerator[str, str]:
                return fn(input)

        extensions = [ui] if ui else []

        return DecoratedAgent(
            id=name,
            name=name,
            url="http://localhost:8001",
            version="1.0.0",
            description=description,
            defaultInputModes=input_content_types,
            defaultOutputModes=output_content_types,
            capabilities=AgentCapabilities(
                streaming=True,
                extensions=extensions,
            ),
            skills=[],
            tags=[],
            examples=[],
        )

    return decorator


class DefaultAgentExecutor(AgentExecutor):
    def __init__(self, agent: RunnableAgent):
        self.agent = agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)
        result_generator = self.agent.run(context.message)

        async for result in result_generator:
            await updater.update_status(
                TaskState.working,
                A2AMessage(
                    role=Role.agent,
                    parts=[
                        Part(
                            root=A2ATextPart(
                                # A2A limitation
                                text=result.content if result.content else "",
                                metadata=result.metadata.model_dump()
                                if result.metadata
                                else None,
                            )
                        )
                    ],
                    messageId=str(uuid.uuid4()),
                    taskId=task.id,
                    contextId=task.contextId,
                ),
            )

        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


class Server:
    def agent(
        self,
        name: str | None = None,
        description: str | None = None,
        input_content_types: list[str] | None = None,
        output_content_types: list[str] | None = None,
        ui: BeeAIUI | None = None,
    ) -> Callable:
        def decorator(fn: Callable) -> Callable:
            runnable_agent = agent_decorator(
                name=name,
                description=description,
                input_content_types=input_content_types,
                output_content_types=output_content_types,
                ui=ui,
            )(fn)
            self.agent_card = runnable_agent
            self.agent = DefaultAgentExecutor(runnable_agent)
            return fn

        return decorator

    def run(self):
        request_handler = DefaultRequestHandler(
            agent_executor=self.agent, task_store=InMemoryTaskStore()
        )

        server = A2AStarletteApplication(
            agent_card=self.agent_card,
            http_handler=request_handler,
        )

        app = server.build()
        app.add_middleware(
          CORSMiddleware,
          allow_origins=["*"],
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
        )

        uvicorn.run(app, host="0.0.0.0", port=8001)
