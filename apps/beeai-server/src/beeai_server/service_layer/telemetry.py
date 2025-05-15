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

from kink import inject

from beeai_server.configuration import Configuration


@inject
class TelemetryService:
    def __init__(
        self,
        # collector_repository: ITelemetryRepository,
        # collector_manager: TelemetryCollectorManager,
        config: Configuration,
    ):
        # self._repository = collector_repository
        # self._manager = collector_manager
        self._config = config

    async def read_config(self):
        raise NotImplementedError
        # config = await self._repository.get()
        # return config

    async def update_config(self, *, sharing_enabled: bool):
        raise NotImplementedError
        # config = await self._repository.get()
        # await self._repository.set(config=config.model_copy(update={"sharing_enabled": sharing_enabled}))
        # await self._manager.reload()
