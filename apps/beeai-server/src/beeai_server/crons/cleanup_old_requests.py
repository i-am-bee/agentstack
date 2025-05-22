# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from datetime import timedelta

from beeai_server.configuration import Configuration
from beeai_server.service_layer.unit_of_work import IUnitOfWorkFactory

from beeai_server.utils.periodic import periodic
from kink import inject

logger = logging.getLogger(__name__)


@periodic(period=timedelta(minutes=5))
@inject
async def clean_up_old_requests(configuration: Configuration, uow: IUnitOfWorkFactory):
    async with uow() as uow:
        deleted_count = await uow.agents.delete_requests_older_than(
            finished_threshold=timedelta(seconds=configuration.persistence.finished_requests_remove_after_sec),
            stale_threshold=timedelta(seconds=configuration.persistence.stale_requests_remove_after_sec),
        )
        await uow.commit()
    if deleted_count:
        logger.info(f"Deleted {deleted_count} old requests")
