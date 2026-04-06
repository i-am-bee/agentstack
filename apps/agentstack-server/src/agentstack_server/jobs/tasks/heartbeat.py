# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from contextlib import suppress
from uuid import UUID, uuid4

from a2a.server.context import ServerCallContext
from a2a.types import Message, MessageSendParams, Part, Role, TextPart
from kink import inject
from procrastinate import Blueprint
from procrastinate.exceptions import AlreadyEnqueued

from agentstack_server.api.auth.auth import issue_internal_jwt
from agentstack_server.configuration import Configuration
from agentstack_server.domain.models.permissions import Permissions
from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.a2a import A2AProxyService
from agentstack_server.service_layer.services.users import UserService
from agentstack_server.service_layer.unit_of_work import IUnitOfWorkFactory

logger = logging.getLogger(__name__)

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.HEARTBEAT))
@inject
async def send_heartbeat(
    context_id: str,
    uow_factory: IUnitOfWorkFactory,
    a2a_proxy: A2AProxyService,
    user_service: UserService,
    configuration: Configuration,
):
    ctx_id = UUID(context_id)

    async with uow_factory() as uow:
        heartbeat = await uow.contexts.get_heartbeat(context_id=ctx_id)

    if not heartbeat or not heartbeat.active:
        return

    async with uow_factory() as uow:
        context = await uow.contexts.get(context_id=ctx_id)
        provider = await uow.providers.get(provider_id=heartbeat.provider_id)

    user = await user_service.get_user(heartbeat.created_by)

    token, _ = issue_internal_jwt(
        user_id=user.id,
        context_id=ctx_id,
        global_permissions=Permissions(a2a_proxy={heartbeat.provider_id}),
        context_permissions=Permissions(context_data={"read", "write"}),
        configuration=configuration,
    )

    server_context = ServerCallContext(state={"headers": {"authorization": f"Bearer {token}"}})
    handler = await a2a_proxy.get_request_handler(provider=provider, user=user)

    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=heartbeat.message))],
            context_id=str(ctx_id),
            message_id=str(uuid4()),
        )
    )

    try:
        await handler.on_message_send(params, context=server_context)
    except Exception:
        logger.warning(f"Heartbeat failed for context {context_id}", exc_info=True)

    async with uow_factory() as uow:
        hb = await uow.contexts.get_heartbeat(context_id=ctx_id)

    if hb and hb.active:
        with suppress(AlreadyEnqueued):
            await send_heartbeat.configure(
                queueing_lock=f"heartbeat:{ctx_id}",
                schedule_in={"seconds": hb.interval_seconds},
            ).defer_async(context_id=context_id)
