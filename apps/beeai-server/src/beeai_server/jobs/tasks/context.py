# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from kink import inject
from procrastinate import Blueprint

from beeai_server.jobs.queues import Queues
from beeai_server.service_layer.services.contexts import ContextService

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.GENERATE_CONVERSATION_TITLE))
@inject
async def generate_conversation_title(context_id: str, context_service: ContextService):
    await context_service.generate_conversation_title(context_id=UUID(context_id))
