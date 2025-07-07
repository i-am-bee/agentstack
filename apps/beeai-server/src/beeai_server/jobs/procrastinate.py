# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
import re

import procrastinate
from kink import inject

from beeai_server.configuration import Configuration
from beeai_server.jobs.crons.cleanup import blueprint as cleanup_crons
from beeai_server.jobs.crons.provider import blueprint as provider_crons
from beeai_server.jobs.tasks.file import blueprint as file_tasks

logger = logging.getLogger(__name__)


@inject
def create_app(configuration: Configuration) -> procrastinate.App:
    conn_string = str(configuration.persistence.db_url.get_secret_value())
    conn_string = re.sub(r"postgresql\+[a-zA-Z]+://", "postgresql://", conn_string)

    def exit_app_on_db_error(*_args, **_kwargs):
        import os
        import signal

        logger.critical("DB is not responding, forcing shutdown")

        os.kill(os.getpid(), signal.SIGTERM)

    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(
            conninfo=conn_string,
            reconnect_failed=exit_app_on_db_error,
            kwargs={
                "options": f"-c search_path={configuration.persistence.procrastinate_schema}",
            },
        ),
    )
    app.add_tasks_from(blueprint=file_tasks, namespace="text_extraction")
    app.add_tasks_from(blueprint=provider_crons, namespace="cron_provider")
    app.add_tasks_from(blueprint=cleanup_crons, namespace="cron_cleanup")
    return app
