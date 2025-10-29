# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from kink import inject
from procrastinate import Blueprint, JobContext

from agentstack_server.jobs.queues import Queues
from agentstack_server.service_layer.services.mcp import McpService

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.TOOLKIT_DELETION), pass_context=True)
@inject
async def delete_toolkit(context: JobContext, toolkit_id: str, mcp_service: McpService):
    await mcp_service.delete_toolkit(toolkit_id=toolkit_id)
