# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import timedelta

from kink import inject
from procrastinate import Blueprint, builtin_tasks, JobContext

from beeai_server.configuration import Configuration
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory


blueprint = Blueprint()

logger = logging.getLogger(__name__)


@blueprint.periodic(cron="*/5 * * * *")
@blueprint.task(queueing_lock="clean_up_old_requests", queue="cron:cleanup")
@inject
async def clean_up_old_requests(timestamp: int, configuration: Configuration, uow: IUnitOfWorkFactory):
    async with uow() as uow:
        deleted_count = await uow.agents.delete_requests_older_than(
            finished_threshold=timedelta(seconds=configuration.persistence.finished_requests_remove_after_sec),
            stale_threshold=timedelta(seconds=configuration.persistence.stale_requests_remove_after_sec),
        )
        await uow.commit()
    if deleted_count:
        logger.info(f"Deleted {deleted_count} old requests")


@blueprint.periodic(cron="*/10 * * * *")
@blueprint.task(queueing_lock="remove_old_jobs", queue="cron:cleanup", pass_context=True)
async def remove_old_jobs(context: JobContext, timestamp: int):
    return await builtin_tasks.remove_old_jobs(
        context,
        max_hours=1,
        remove_failed=True,
        remove_cancelled=True,
        remove_aborted=True,
    )
