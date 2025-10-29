# Copyright 2025 © Agent Stack a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from datetime import timedelta

from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.apps.jsonrpc import A2AFastAPIApplication
from a2a.server.apps.rest import A2ARESTFastAPIApplication
from a2a.server.events import InMemoryQueueManager, QueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, PushNotificationConfigStore, PushNotificationSender, TaskStore
from a2a.types import AgentInterface, TransportProtocol
from fastapi import APIRouter, Depends, FastAPI
from fastapi.applications import AppType
from starlette.types import Lifespan

from agentstack_sdk.server.agent import Agent, Executor
from agentstack_sdk.server.store.context_store import ContextStore
from agentstack_sdk.server.store.memory_context_store import InMemoryContextStore


def create_app(
    agent: Agent,
    task_store: TaskStore | None = None,
    context_store: ContextStore | None = None,
    queue_manager: QueueManager | None = None,
    push_config_store: PushNotificationConfigStore | None = None,
    push_sender: PushNotificationSender | None = None,
    request_context_builder: RequestContextBuilder | None = None,
    lifespan: Lifespan[AppType] | None = None,
    dependencies: list[Depends] | None = None,  # pyright: ignore [reportGeneralTypeIssues]
    override_interfaces: bool = True,
    task_timeout: timedelta = timedelta(minutes=10),
    **kwargs,
) -> FastAPI:
    queue_manager = queue_manager or InMemoryQueueManager()
    task_store = task_store or InMemoryTaskStore()
    context_store = context_store or InMemoryContextStore()
    http_handler = DefaultRequestHandler(
        agent_executor=Executor(agent.execute, queue_manager, context_store=context_store, task_timeout=task_timeout),
        task_store=task_store,
        queue_manager=queue_manager,
        push_config_store=push_config_store,
        push_sender=push_sender,
        request_context_builder=request_context_builder,
    )

    if override_interfaces:
        agent.card.additional_interfaces = [
            AgentInterface(url=agent.card.url, transport=TransportProtocol.http_json),
            AgentInterface(url=agent.card.url + "/jsonrpc/", transport=TransportProtocol.jsonrpc),
        ]
        agent.card.url = agent.card.url + "/jsonrpc/"
        agent.card.preferred_transport = TransportProtocol.jsonrpc

    jsonrpc_app = A2AFastAPIApplication(agent_card=agent.card, http_handler=http_handler).build(
        dependencies=dependencies,
        **kwargs,
    )

    rest_app = A2ARESTFastAPIApplication(agent_card=agent.card, http_handler=http_handler).build(
        dependencies=dependencies,
        **kwargs,
    )

    rest_app.mount("/jsonrpc", jsonrpc_app)
    rest_app.include_router(APIRouter(lifespan=lifespan))
    return rest_app
