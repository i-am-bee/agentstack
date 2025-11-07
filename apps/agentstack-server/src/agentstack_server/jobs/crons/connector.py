# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import logging

from kink import inject
from procrastinate import Blueprint

from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.connector import ConnectorService

logger = logging.getLogger(__name__)

blueprint = Blueprint()


@blueprint.periodic(cron="* * * * * */30")
@blueprint.task(queueing_lock="refresh_connectors", queue=str(Queues.CRON_CONNECTOR))
@inject
async def refresh_connectors(timestamp: int, service: ConnectorService):
    async with asyncio.TaskGroup() as tg:
        for connector in await service.list_connectors():
            tg.create_task(service.refresh_connector(connector_id=connector.id))
