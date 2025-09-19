# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from kink import inject
from procrastinate import Blueprint, JobContext

from beeai_server.jobs.queues import Queues
from beeai_server.service_layer.services.files import FileService

blueprint = Blueprint()


@blueprint.task(queue=str(Queues.TEXT_EXTRACTION), pass_context=True)
@inject
async def extract_text(context: JobContext, file_id: str, file_service: FileService):
    await file_service.extract_text(file_id=UUID(file_id), job_id=str(context.job.id))
