# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.events import InMemoryQueueManager, QueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, PushNotificationConfigStore, PushNotificationSender, TaskStore
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH, DEFAULT_RPC_URL, EXTENDED_AGENT_CARD_PATH
from fastapi import APIRouter, Depends, FastAPI
from fastapi.applications import AppType
from starlette.types import Lifespan

from beeai_sdk.server.agent import Agent, Executor


def create_app(
    agent: Agent,
    task_store: TaskStore | None = None,
    queue_manager: QueueManager | None = None,
    push_config_store: PushNotificationConfigStore | None = None,
    push_sender: PushNotificationSender | None = None,
    request_context_builder: RequestContextBuilder | None = None,
    lifespan: Lifespan[AppType] | None = None,
    dependencies: list[Depends] | None = None,  # pyright: ignore [reportGeneralTypeIssues]
    **kwargs,
) -> FastAPI:
    queue_manager = queue_manager or InMemoryQueueManager()
    task_store = task_store or InMemoryTaskStore()
    app = A2AFastAPIApplication(
        agent_card=agent.card,
        http_handler=DefaultRequestHandler(
            agent_executor=Executor(agent.execute, queue_manager),
            task_store=task_store,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
            request_context_builder=request_context_builder,
        ),
    ).build(
        rpc_url=DEFAULT_RPC_URL,
        agent_card_url=AGENT_CARD_WELL_KNOWN_PATH,
        extended_agent_card_url=EXTENDED_AGENT_CARD_PATH,
        dependencies=dependencies,
        **kwargs,
    )

    app.include_router(APIRouter(lifespan=lifespan))
    return app
