# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from kink import inject
from procrastinate import Blueprint, JobContext

from beeai_server.service_layer.services.mcp import McpService

blueprint = Blueprint()


@blueprint.task(queue="toolkit_deletion", pass_context=True)
@inject
async def delete_toolkit(context: JobContext, toolkit_id: str, mcp_service: McpService):
    await mcp_service.delete_toolkit(toolkit_id=toolkit_id)
