# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import timedelta

from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.apps.jsonrpc import A2AFastAPIApplication
from a2a.server.apps.rest import A2ARESTFastAPIApplication
from a2a.server.events import InMemoryQueueManager, QueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    InMemoryTaskStore,
    PushNotificationConfigStore,
    PushNotificationSender,
    TaskStore,
)
from a2a.types import AgentInterface
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT
from fastapi import APIRouter, FastAPI
from fastapi.applications import AppType
from fastapi.params import Depends
from starlette.types import Lifespan

from agentstack_sdk.a2a.extensions import BaseExtensionServer
from agentstack_sdk.server.agent import Agent, Executor
from agentstack_sdk.server.constants import DEFAULT_IMPLICIT_EXTENSIONS
from agentstack_sdk.server.store.context_store import ContextStore
from agentstack_sdk.server.store.memory_context_store import InMemoryContextStore
from agentstack_sdk.types import SdkAuthenticationBackend


def create_app(
    agent: Agent,
    url: str,
    task_store: TaskStore | None = None,
    context_store: ContextStore | None = None,
    implicit_extensions: dict[str, BaseExtensionServer] = DEFAULT_IMPLICIT_EXTENSIONS,
    required_extensions: set[str] | None = None,
    auth_backend: SdkAuthenticationBackend | None = None,
    queue_manager: QueueManager | None = None,
    push_config_store: PushNotificationConfigStore | None = None,
    push_sender: PushNotificationSender | None = None,
    request_context_builder: RequestContextBuilder | None = None,
    lifespan: Lifespan[AppType] | None = None,
    dependencies: list[Depends] | None = None,
    task_timeout: timedelta = timedelta(minutes=10),
    **kwargs,
) -> FastAPI:
    queue_manager = queue_manager or InMemoryQueueManager()
    task_store = task_store or InMemoryTaskStore()
    context_store = context_store or InMemoryContextStore()
    http_handler = DefaultRequestHandler(
        agent_executor=Executor(
            agent,
            queue_manager,
            context_store=context_store,
            task_timeout=task_timeout,
            task_store=task_store,
        ),
        task_store=task_store,
        queue_manager=queue_manager,
        push_config_store=push_config_store,
        push_sender=push_sender,
        request_context_builder=request_context_builder,
    )
    protocol_version = PROTOCOL_VERSION_CURRENT

    agent.initialize(
        a2a_security=auth_backend.get_card_security_schemes() if auth_backend else None,
        supported_interfaces=[
            AgentInterface(url=url, protocol_binding="HTTP+JSON", protocol_version=protocol_version),
            AgentInterface(url=url + "/jsonrpc/", protocol_binding="JSONRPC", protocol_version=protocol_version),
        ],
        implicit_extensions=implicit_extensions,
        required_extensions=(required_extensions or set()) | context_store.required_extensions,
    )

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
