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

import re

import procrastinate
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.jobs.tasks.file import blueprint as file_tasks
from beeai_server.jobs.crons.provider import blueprint as provider_crons
from beeai_server.jobs.crons.cleanup import blueprint as cleanup_crons


@inject
def create_app(configuration: Configuration) -> procrastinate.App:
    conn_string = str(configuration.persistence.db_url.get_secret_value())
    conn_string = re.sub("postgresql\+[a-zA-Z]+://", "postgresql://", conn_string)
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(
            conninfo=conn_string,
            kwargs={
                "options": f"-c search_path={configuration.persistence.procrastinate_schema}",
            },
        ),
    )
    app.add_tasks_from(blueprint=file_tasks, namespace="text_extraction")
    app.add_tasks_from(blueprint=provider_crons, namespace="cron_provider")
    app.add_tasks_from(blueprint=cleanup_crons, namespace="cron_acp")
    return app
